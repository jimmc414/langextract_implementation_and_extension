"""
Command-line interface for LangExtract
"""

import click
import os
import sys
import json
import yaml
from typing import Optional
import langextract as lx
from langextract import data
from . import (
    load_document_from_url, 
    load_documents_from_csv,
    export_to_gif,
    create_simple_gif,
    multi_pass_extract,
    MultiPassStrategies,
    extract as enhanced_extract,
    ReferenceResolver,
    RelationshipResolver,
    ExtractionAnnotator,
    list_providers,
    list_patterns
)
from .templates import (
    TemplateManager,
    get_builtin_template,
    list_builtin_templates
)
from .template_builder import (
    TemplateWizard,
    TemplateBuilder,
    extract_with_template
)


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """LangExtract CLI - Extract structured information from documents with grounding."""
    pass


@cli.command()
@click.option('--input', '-i', required=True, help='Input file path, URL, or "-" for stdin')
@click.option('--output', '-o', default='output.html', help='Output file (default: output.html)')
@click.option('--format', '-f', type=click.Choice(['html', 'jsonl', 'csv', 'gif']), 
              default='html', help='Output format')
@click.option('--model', '-m', default='gemini-2.5-flash-thinking', help='Model ID to use (default: Flash 2.5 with thinking)')
@click.option('--prompt', '-p', help='Extraction prompt description')
@click.option('--template', help='Template ID or path to use for extraction')
@click.option('--examples', '-e', help='Path to examples file (JSON/YAML)')
@click.option('--api-key', '-k', envvar='GOOGLE_API_KEY', help='API key (or use GOOGLE_API_KEY env var)')
@click.option('--temperature', '-t', default=0.3, type=float, help='Generation temperature (0.0-2.0)')
@click.option('--fetch-urls', is_flag=True, help='Fetch content from URLs automatically')
@click.option('--resolve-refs', is_flag=True, help='Resolve references and relationships')
@click.option('--annotate', is_flag=True, help='Add quality annotations')
@click.option('--debug', is_flag=True, help='Enable debug output')
def extract(input, output, format, model, prompt, template, examples, api_key, temperature, fetch_urls, resolve_refs, annotate, debug):
    """
    Extract information from a document.
    
    Examples:
    
        # Extract from a local file
        langextract extract -i document.pdf -p "Extract names and amounts" -o results.html
        
        # Extract using a template
        langextract extract -i invoice.pdf --template invoice -o results.html
        
        # Extract from a URL
        langextract extract -i https://example.com/doc.pdf -p "Extract dates" -o dates.jsonl
        
        # Extract from stdin
        cat document.txt | langextract extract -i - -p "Extract addresses" -f csv
    """
    # Validate that either prompt or template is provided
    if not prompt and not template:
        click.echo("Error: Either --prompt or --template must be provided", err=True)
        sys.exit(1)
    
    # Set API key if provided
    if api_key:
        os.environ['GOOGLE_API_KEY'] = api_key
    
    # Load examples if provided
    example_data = []
    if examples:
        try:
            with open(examples, 'r') as f:
                if examples.endswith('.yaml') or examples.endswith('.yml'):
                    examples_dict = yaml.safe_load(f)
                else:
                    examples_dict = json.load(f)
            
            # Convert to ExampleData objects
            for ex in examples_dict.get('examples', []):
                extractions = []
                for ext in ex.get('extractions', []):
                    extractions.append(data.Extraction(
                        extraction_class=ext['class'],
                        extraction_text=ext['text'],
                        attributes=ext.get('attributes')
                    ))
                example_data.append(data.ExampleData(
                    text=ex['text'],
                    extractions=extractions
                ))
        except Exception as e:
            click.echo(f"Error loading examples: {e}", err=True)
            sys.exit(1)
    
    # Load document
    try:
        if input == '-':
            # Read from stdin
            text = sys.stdin.read()
            doc = data.Document(text=text, document_id='stdin')
        elif input.startswith('http://') or input.startswith('https://'):
            # Load from URL
            click.echo(f"Loading from URL: {input}")
            doc = load_document_from_url(input)
        else:
            # Load from file
            if not os.path.exists(input):
                click.echo(f"Error: File not found: {input}", err=True)
                sys.exit(1)
            
            with open(input, 'r', encoding='utf-8') as f:
                text = f.read()
            doc = data.Document(text=text, document_id=input)
    
    except Exception as e:
        click.echo(f"Error loading input: {e}", err=True)
        sys.exit(1)
    
    # Perform extraction with new features
    click.echo(f"Extracting with model: {model} (temperature: {temperature})")
    try:
        # Use template if provided
        if template:
            click.echo(f"Using template: {template}")
            result = extract_with_template(
                document=doc,
                template=template,
                model_id=model,
                temperature=temperature,
                api_key=api_key,
                debug=debug
            )
        # Use enhanced extract if URL fetching or temperature is specified
        elif fetch_urls or temperature != 0.3:
            result = enhanced_extract(
                text_or_documents=doc,
                prompt_description=prompt,
                examples=example_data,
                model_id=model,
                temperature=temperature,
                fetch_urls=fetch_urls,
                api_key=api_key,
                debug=debug
            )
        else:
            result = lx.extract(
                text_or_documents=doc,
                prompt_description=prompt,
                examples=example_data,
                model_id=model,
                api_key=api_key,
                debug=debug
            )
        
        # Apply resolver if requested
        if resolve_refs and result.extractions:
            click.echo("Resolving references...")
            resolver = ReferenceResolver()
            result.extractions = resolver.resolve_references(result.extractions, result.text)
            
            rel_resolver = RelationshipResolver()
            relationships = rel_resolver.resolve_relationships(result.extractions, result.text)
            if relationships:
                click.echo(f"Found {len(relationships)} relationships")
        
        # Apply annotations if requested
        if annotate and result.extractions:
            click.echo("Adding annotations...")
            annotator = ExtractionAnnotator()
            for extraction in result.extractions:
                annotator.annotate_extraction(extraction, result.text, result.extractions)
            
            # Add annotations to result
            result.annotations = annotator.export_annotations()
            click.echo(f"Added {len(annotator.annotations)} annotations")
            
    except Exception as e:
        click.echo(f"Extraction error: {e}", err=True)
        sys.exit(1)
    
    # Save output
    try:
        if format == 'html':
            # Save JSONL first
            jsonl_path = output.replace('.html', '.jsonl')
            lx.io.save_annotated_documents([result], output_name=jsonl_path)
            # Generate HTML
            html = lx.visualize(jsonl_path)
            with open(output, 'w') as f:
                f.write(html)
            click.echo(f"✓ Created HTML visualization: {output}")
            
        elif format == 'jsonl':
            lx.io.save_annotated_documents([result], output_name=output)
            click.echo(f"✓ Saved JSONL: {output}")
            
        elif format == 'csv':
            from .csv_loader import save_extractions_to_csv
            save_extractions_to_csv([result], output)
            click.echo(f"✓ Saved CSV: {output}")
            
        elif format == 'gif':
            # Save JSONL first
            jsonl_path = output.replace('.gif', '.jsonl')
            lx.io.save_annotated_documents([result], output_name=jsonl_path)
            # Create GIF
            create_simple_gif(jsonl_path, output)
            click.echo(f"✓ Created GIF: {output}")
            
    except Exception as e:
        click.echo(f"Error saving output: {e}", err=True)
        sys.exit(1)
    
    # Print summary
    click.echo(f"\nExtracted {len(result.extractions)} items:")
    by_class = {}
    for ext in result.extractions:
        by_class[ext.extraction_class] = by_class.get(ext.extraction_class, 0) + 1
    
    for class_name, count in sorted(by_class.items()):
        click.echo(f"  {class_name}: {count}")


@cli.command()
@click.option('--csv', '-c', required=True, help='Input CSV file')
@click.option('--text-column', '-t', required=True, help='Column containing text')
@click.option('--id-column', '-i', help='Column containing document IDs')
@click.option('--output', '-o', default='batch_results.csv', help='Output CSV file')
@click.option('--prompt', '-p', required=True, help='Extraction prompt')
@click.option('--model', '-m', default='gemini-2.5-flash-thinking', help='Model ID (default: Flash 2.5 with thinking)')
@click.option('--max-rows', '-n', type=int, help='Maximum rows to process')
@click.option('--examples', '-e', help='Path to examples file')
def batch(csv, text_column, id_column, output, prompt, model, max_rows, examples):
    """
    Process a batch of documents from CSV.
    
    Example:
        langextract batch -c reviews.csv -t review_text -p "Extract product names and sentiment"
    """
    # Load examples
    example_data = []
    if examples:
        # (Same loading logic as extract command)
        pass
    
    try:
        from .csv_loader import process_csv_batch
        process_csv_batch(
            csv,
            text_column,
            prompt,
            example_data,
            output,
            model_id=model,
            max_rows=max_rows
        )
    except Exception as e:
        click.echo(f"Batch processing error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--input', '-i', required=True, help='Input text file or "-" for stdin')
@click.option('--strategy', '-s', 
              type=click.Choice(['legal', 'medical', 'financial', 'custom']),
              default='custom', help='Multi-pass strategy')
@click.option('--passes', '-p', help='Custom passes config (JSON/YAML)')
@click.option('--output', '-o', default='multipass_results.html', help='Output file')
@click.option('--model', '-m', default='gemini-2.5-flash-thinking', help='Model ID (default: Flash 2.5 with thinking)')
@click.option('--debug', is_flag=True, help='Enable debug output')
def multipass(input, strategy, passes, output, model, debug):
    """
    Perform multi-pass extraction for improved recall.
    
    Examples:
        # Use preset strategy
        langextract multipass -i judgment.txt -s legal -o results.html
        
        # Use custom passes
        langextract multipass -i document.txt -p passes.yaml -o results.html
    """
    # Load document
    if input == '-':
        text = sys.stdin.read()
    else:
        with open(input, 'r') as f:
            text = f.read()
    
    # Get passes configuration
    if strategy == 'custom' and passes:
        with open(passes, 'r') as f:
            if passes.endswith('.yaml') or passes.endswith('.yml'):
                passes_config = yaml.safe_load(f)['passes']
            else:
                passes_config = json.load(f)['passes']
    else:
        # Use preset strategy
        if strategy == 'legal':
            passes_config = MultiPassStrategies.legal_document_strategy()
        elif strategy == 'medical':
            passes_config = MultiPassStrategies.medical_record_strategy()
        elif strategy == 'financial':
            passes_config = MultiPassStrategies.financial_document_strategy()
        else:
            click.echo("Error: Must specify --strategy or --passes", err=True)
            sys.exit(1)
    
    # Perform multi-pass extraction
    try:
        result = multi_pass_extract(
            text,
            passes_config,
            model_id=model,
            debug=debug
        )
        
        # Save results
        if output.endswith('.html'):
            jsonl_path = output.replace('.html', '.jsonl')
            lx.io.save_annotated_documents([result], output_name=jsonl_path)
            html = lx.visualize(jsonl_path)
            with open(output, 'w') as f:
                f.write(html)
        else:
            lx.io.save_annotated_documents([result], output_name=output)
        
        click.echo(f"✓ Saved results: {output}")
        click.echo(f"Total extractions: {len(result.extractions)}")
        
    except Exception as e:
        click.echo(f"Multi-pass error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--jsonl', '-j', required=True, help='Input JSONL file')
@click.option('--output', '-o', default='visualization.html', help='Output file')
@click.option('--format', '-f', 
              type=click.Choice(['html', 'gif', 'frames']),
              default='html', help='Output format')
@click.option('--template', '-t',
              type=click.Choice(['standard', 'dark', 'minimal', 'compact']),
              default='standard', help='HTML template style')
def visualize(jsonl, output, format, template):
    """
    Create visualization from JSONL file.
    
    Examples:
        # Create HTML with default template
        langextract visualize -j results.jsonl -o viz.html
        
        # Create HTML with dark mode template
        langextract visualize -j results.jsonl -o viz.html -t dark
        
        # Create GIF
        langextract visualize -j results.jsonl -f gif -o animation.gif
    """
    try:
        if format == 'html':
            if template == 'standard':
                html = lx.visualize(jsonl)
            else:
                from .custom_visualization import (
                    visualize_with_template,
                    DarkModeTemplate,
                    MinimalTemplate,
                    CompactTemplate
                )
                
                template_map = {
                    'dark': DarkModeTemplate(),
                    'minimal': MinimalTemplate(),
                    'compact': CompactTemplate()
                }
                
                html = visualize_with_template(jsonl, template=template_map[template])
            
            with open(output, 'w') as f:
                f.write(html)
            click.echo(f"✓ Created HTML ({template} template): {output}")
            
        elif format == 'gif':
            create_simple_gif(jsonl, output)
            click.echo(f"✓ Created GIF: {output}")
            
        elif format == 'frames':
            from .gif_export import export_to_html_frames
            frames = export_to_html_frames(jsonl, output)
            click.echo(f"✓ Created {len(frames)} frames in: {output}/")
            
    except Exception as e:
        click.echo(f"Visualization error: {e}", err=True)
        sys.exit(1)


@cli.command()
def providers():
    """List available providers and supported models."""
    click.echo("Available Providers")
    click.echo("==================\n")
    
    # List providers
    providers = list_providers()
    for name, provider_class in providers.items():
        click.echo(f"• {name}")
        if hasattr(provider_class, 'get_supported_models'):
            models = provider_class.get_supported_models()
            if models:
                for model in models[:5]:  # Show first 5 models
                    click.echo(f"  - {model}")
                if len(models) > 5:
                    click.echo(f"  ... and {len(models)-5} more")
        click.echo()
    
    # List patterns
    click.echo("\nModel ID Patterns")
    click.echo("=================\n")
    patterns = list_patterns()
    for pattern in patterns:
        click.echo(f"• {pattern}")
    
    click.echo("\nTo use a provider, specify the model ID with -m flag:")
    click.echo("langextract extract -i doc.txt -p 'Extract data' -m gemini-1.5-flash")


@cli.command()
def examples():
    """Show example usage and create example files."""
    click.echo("""
LangExtract Examples
===================

1. Basic extraction from PDF:
   langextract extract -i document.pdf -p "Extract names and dates" -o results.html

2. Extract using a template:
   langextract extract -i invoice.pdf --template invoice -o results.html
   langextract extract -i resume.pdf --template resume -o candidates.jsonl

3. Extract from URL with automatic fetching:
   langextract extract -i https://example.com/doc.pdf -p "Extract amounts" --fetch-urls -o amounts.jsonl

4. Extract with custom temperature:
   langextract extract -i doc.txt -p "Extract creative insights" -t 0.7 -o insights.html

5. Extract with reference resolution:
   langextract extract -i legal.txt -p "Extract entities" --resolve-refs -o entities.html

6. Extract with quality annotations:
   langextract extract -i report.pdf -p "Extract findings" --annotate -o annotated.jsonl

7. Batch process CSV:
   langextract batch -c documents.csv -t content -p "Extract entities" -o results.csv

8. Multi-pass extraction:
   langextract multipass -i legal.txt -s legal -o legal_results.html

9. Template management:
   langextract template list                                    # List all templates
   langextract template list -v                                 # List with details
   langextract template show invoice                            # Show template details
   langextract template create -i                               # Interactive wizard
   langextract template create -e examples.yaml -n "My Template"  # From examples
   langextract template export invoice -o invoice_template.yaml   # Export template
   langextract template import custom_template.yaml             # Import template
   langextract template delete my_template                      # Delete template

10. Create visualization:
    langextract visualize -j results.jsonl -o viz.html
    langextract visualize -j results.jsonl -o viz.html -t dark
    langextract visualize -j results.jsonl -f gif -o animation.gif

11. List available providers:
    langextract providers

Example files have been created:
- example_prompts.yaml
- example_passes.yaml
- example_template.yaml
""")
    
    # Create example files
    example_prompts = {
        'examples': [
            {
                'text': 'Invoice #12345 dated January 15, 2025',
                'extractions': [
                    {'class': 'invoice_number', 'text': '#12345'},
                    {'class': 'date', 'text': 'January 15, 2025'}
                ]
            }
        ]
    }
    
    example_passes = {
        'passes': [
            {
                'prompt_description': 'Extract all person names',
                'focus_on': ['person', 'name']
            },
            {
                'prompt_description': 'Extract all monetary amounts',
                'focus_on': ['amount', 'money', 'price']
            }
        ]
    }
    
    with open('example_prompts.yaml', 'w') as f:
        yaml.dump(example_prompts, f)
    
    with open('example_passes.yaml', 'w') as f:
        yaml.dump(example_passes, f)
    
    # Create example template file
    example_template = {
        'template_id': 'custom_contract',
        'name': 'Contract Analysis Template',
        'description': 'Extract key information from contracts',
        'document_type': 'legal',
        'fields': [
            {
                'name': 'party1',
                'extraction_class': 'organization',
                'description': 'First party in the contract',
                'required': True,
                'examples': ['ABC Corporation', 'John Smith Ltd.']
            },
            {
                'name': 'party2',
                'extraction_class': 'organization',
                'description': 'Second party in the contract',
                'required': True,
                'examples': ['XYZ Inc.', 'Jane Doe Enterprises']
            },
            {
                'name': 'effective_date',
                'extraction_class': 'date',
                'description': 'Contract effective date',
                'required': True,
                'validation_pattern': r'\d{4}-\d{2}-\d{2}'
            },
            {
                'name': 'term_length',
                'extraction_class': 'text',
                'description': 'Duration of the contract',
                'required': False,
                'examples': ['12 months', '3 years', 'perpetual']
            },
            {
                'name': 'total_value',
                'extraction_class': 'amount',
                'description': 'Total contract value',
                'required': False,
                'examples': ['$100,000', '€50,000']
            }
        ],
        'preferred_model': 'gemini-1.5-flash',
        'temperature': 0.2,
        'tags': ['legal', 'contract', 'analysis'],
        'author': 'example',
        'version': '1.0.0'
    }
    
    with open('example_template.yaml', 'w') as f:
        yaml.dump(example_template, f, default_flow_style=False)


@cli.group()
def template():
    """Manage extraction templates."""
    pass


@template.command('list')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed template information')
def template_list(verbose):
    """
    List available templates.
    
    Examples:
        langextract template list
        langextract template list -v
    """
    click.echo("Built-in Templates")
    click.echo("==================\n")
    
    builtin = list_builtin_templates()
    for template_id in builtin:
        template = get_builtin_template(template_id)
        click.echo(f"• {template_id}")
        if verbose:
            click.echo(f"  Name: {template.name}")
            click.echo(f"  Description: {template.description}")
            click.echo(f"  Fields: {', '.join(f.name for f in template.fields)}")
            click.echo()
    
    click.echo("\nCustom Templates")
    click.echo("================\n")
    
    manager = TemplateManager()
    custom = manager.list_templates()
    
    if custom:
        for template_id in custom:
            template = manager.load_template(template_id)
            if template:
                click.echo(f"• {template_id}")
                if verbose:
                    click.echo(f"  Name: {template.name}")
                    click.echo(f"  Description: {template.description}")
                    click.echo(f"  Fields: {', '.join(f.name for f in template.fields)}")
                    click.echo()
    else:
        click.echo("No custom templates found.")
    
    click.echo("\nTo use a template:")
    click.echo("langextract extract -i document.pdf --template <template_id>")


@template.command('show')
@click.argument('template_id')
@click.option('--format', '-f', type=click.Choice(['yaml', 'json']), default='yaml', 
              help='Output format')
def template_show(template_id, format):
    """
    Show details of a specific template.
    
    Examples:
        langextract template show invoice
        langextract template show invoice -f json
    """
    # Try built-in first
    template = get_builtin_template(template_id)
    
    # Then try custom
    if not template:
        manager = TemplateManager()
        template = manager.load_template(template_id)
    
    if not template:
        click.echo(f"Template not found: {template_id}", err=True)
        sys.exit(1)
    
    # Convert to dict
    template_dict = {
        'template_id': template.template_id,
        'name': template.name,
        'description': template.description,
        'document_type': template.document_type.value,
        'fields': [
            {
                'name': f.name,
                'extraction_class': f.extraction_class,
                'description': f.description,
                'required': f.required,
                'examples': f.examples,
                'validation_pattern': f.validation_pattern
            }
            for f in template.fields
        ],
        'preferred_model': template.preferred_model,
        'temperature': template.temperature,
        'tags': template.tags,
        'author': template.author,
        'version': template.version
    }
    
    if format == 'json':
        click.echo(json.dumps(template_dict, indent=2))
    else:
        click.echo(yaml.dump(template_dict, default_flow_style=False))


@template.command('create')
@click.option('--interactive', '-i', is_flag=True, help='Use interactive wizard')
@click.option('--from-examples', '-e', help='Create from examples file (JSON/YAML)')
@click.option('--name', '-n', help='Template name')
@click.option('--output', '-o', help='Save to file instead of template directory')
def template_create(interactive, from_examples, name, output):
    """
    Create a new extraction template.
    
    Examples:
        # Interactive wizard
        langextract template create -i
        
        # From examples
        langextract template create -e examples.yaml -n "My Template"
        
        # Save to file
        langextract template create -i -o my_template.yaml
    """
    if interactive:
        # Run interactive wizard
        template = TemplateWizard.run()
        
    elif from_examples:
        if not name:
            click.echo("Error: --name is required when using --from-examples", err=True)
            sys.exit(1)
        
        # Load examples
        try:
            with open(from_examples, 'r') as f:
                if from_examples.endswith('.yaml') or from_examples.endswith('.yml'):
                    examples_data = yaml.safe_load(f)
                else:
                    examples_data = json.load(f)
            
            documents = examples_data.get('documents', [])
            extractions = examples_data.get('extractions', [])
            
            if not documents or not extractions:
                click.echo("Error: Examples file must contain 'documents' and 'extractions'", err=True)
                sys.exit(1)
            
            # Build template from examples
            builder = TemplateBuilder()
            template = builder.build_from_examples(
                example_documents=documents,
                expected_extractions=extractions,
                template_name=name
            )
            
            click.echo(f"✓ Created template from {len(documents)} examples")
            
        except Exception as e:
            click.echo(f"Error creating template: {e}", err=True)
            sys.exit(1)
    
    else:
        click.echo("Error: Use --interactive or --from-examples", err=True)
        sys.exit(1)
    
    # Save template
    if output:
        # Save to file
        template_dict = template.to_dict()
        if output.endswith('.json'):
            with open(output, 'w') as f:
                json.dump(template_dict, f, indent=2)
        else:
            with open(output, 'w') as f:
                yaml.dump(template_dict, f, default_flow_style=False)
        click.echo(f"✓ Saved template to: {output}")
    else:
        # Save to template directory
        manager = TemplateManager()
        manager.save_template(template)
        click.echo(f"✓ Saved template: {template.template_id}")


@template.command('delete')
@click.argument('template_id')
@click.confirmation_option(prompt='Are you sure you want to delete this template?')
def template_delete(template_id):
    """
    Delete a custom template.
    
    Example:
        langextract template delete my_template
    """
    manager = TemplateManager()
    
    if manager.delete_template(template_id):
        click.echo(f"✓ Deleted template: {template_id}")
    else:
        click.echo(f"Error: Template not found or is built-in: {template_id}", err=True)
        sys.exit(1)


@template.command('export')
@click.argument('template_id')
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--format', '-f', type=click.Choice(['yaml', 'json']), default='yaml',
              help='Output format')
def template_export(template_id, output, format):
    """
    Export a template to a file.
    
    Examples:
        langextract template export invoice -o invoice_template.yaml
        langextract template export invoice -o invoice_template.json -f json
    """
    # Try built-in first
    template = get_builtin_template(template_id)
    
    # Then try custom
    if not template:
        manager = TemplateManager()
        template = manager.load_template(template_id)
    
    if not template:
        click.echo(f"Template not found: {template_id}", err=True)
        sys.exit(1)
    
    # Export
    template_dict = template.to_dict()
    
    if format == 'json':
        with open(output, 'w') as f:
            json.dump(template_dict, f, indent=2)
    else:
        with open(output, 'w') as f:
            yaml.dump(template_dict, f, default_flow_style=False)
    
    click.echo(f"✓ Exported template to: {output}")


@template.command('import')
@click.argument('file_path')
@click.option('--template-id', help='Override template ID')
def template_import(file_path, template_id):
    """
    Import a template from a file.
    
    Examples:
        langextract template import template.yaml
        langextract template import template.json --template-id custom_invoice
    """
    try:
        with open(file_path, 'r') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                template_dict = yaml.safe_load(f)
            else:
                template_dict = json.load(f)
        
        # Override template ID if provided
        if template_id:
            template_dict['template_id'] = template_id
        
        # Create template from dict
        from .templates import ExtractionTemplate, ExtractionField, DocumentType
        
        fields = []
        for field_dict in template_dict.get('fields', []):
            fields.append(ExtractionField(
                name=field_dict['name'],
                extraction_class=field_dict['extraction_class'],
                description=field_dict.get('description', ''),
                required=field_dict.get('required', True),
                examples=field_dict.get('examples', []),
                validation_pattern=field_dict.get('validation_pattern')
            ))
        
        template = ExtractionTemplate(
            template_id=template_dict['template_id'],
            name=template_dict['name'],
            description=template_dict.get('description', ''),
            document_type=DocumentType(template_dict.get('document_type', 'custom')),
            fields=fields,
            preferred_model=template_dict.get('preferred_model', 'gemini-1.5-flash'),
            temperature=template_dict.get('temperature', 0.3),
            tags=template_dict.get('tags', []),
            author=template_dict.get('author', 'imported'),
            version=template_dict.get('version', '1.0.0')
        )
        
        # Save template
        manager = TemplateManager()
        manager.save_template(template)
        
        click.echo(f"✓ Imported template: {template.template_id}")
        
    except Exception as e:
        click.echo(f"Error importing template: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
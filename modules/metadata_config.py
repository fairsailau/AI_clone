import streamlit as st
import logging
import json
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def metadata_config():
    """
    Configure metadata extraction parameters
    """
    st.title("Metadata Configuration")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    if not st.session_state.selected_files:
        st.warning("No files selected. Please select files in the File Browser first.")
        if st.button("Go to File Browser", key="go_to_file_browser_button_config"):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    # Check if document categorization has been performed
    has_categorization = (
        hasattr(st.session_state, "document_categorization") and 
        st.session_state.document_categorization.get("is_categorized", False)
    )
    
    # Display document categorization results if available
    if has_categorization:
        st.subheader("Document Categorization Results")
        
        # Create a table of document types
        categorization_data = []
        for file in st.session_state.selected_files:
            file_id = file["id"]
            file_name = file["name"]
            
            # Get document type from categorization results
            document_type = "Not categorized"
            if file_id in st.session_state.document_categorization["results"]:
                document_type = st.session_state.document_categorization["results"][file_id]["document_type"]
            
            categorization_data.append({
                "File Name": file_name,
                "Document Type": document_type
            })
        
        # Display table
        st.table(categorization_data)
    else:
        st.info("Document categorization has not been performed. You can categorize documents in the Document Categorization page.")
        if st.button("Go to Document Categorization", key="go_to_doc_cat_button"):
            st.session_state.current_page = "Document Categorization"
            st.rerun()
    
    # Extraction method selection
    st.subheader("Extraction Method")
    
    # Ensure extraction_method is initialized in metadata_config
    if "extraction_method" not in st.session_state.metadata_config:
        st.session_state.metadata_config["extraction_method"] = "freeform"
        
    extraction_method = st.radio(
        "Select extraction method",
        ["Freeform", "Structured"],
        index=0 if st.session_state.metadata_config["extraction_method"] == "freeform" else 1,
        key="extraction_method_radio",
        help="Choose between freeform extraction (free text) or structured extraction (with template)"
    )
    
    # Update extraction method in session state
    st.session_state.metadata_config["extraction_method"] = extraction_method.lower()
    
    # Freeform extraction configuration
    if extraction_method == "Freeform":
        st.subheader("Freeform Extraction Configuration")
        
        # Freeform prompt
        freeform_prompt = st.text_area(
            "Freeform prompt",
            value=st.session_state.metadata_config["freeform_prompt"],
            height=150,
            key="freeform_prompt_textarea",
            help="Prompt for freeform extraction. Be specific about what metadata to extract."
        )
        
        # Update freeform prompt in session state
        st.session_state.metadata_config["freeform_prompt"] = freeform_prompt
        
        # Document type specific prompts
        if has_categorization:
            st.subheader("Document Type Specific Prompts")
            st.info("You can customize the freeform prompt for each document type.")
            
            # Get unique document types
            document_types = set()
            for file_id, result in st.session_state.document_categorization["results"].items():
                document_types.add(result["document_type"])
            
            # Initialize document type prompts if not exists
            if "document_type_prompts" not in st.session_state.metadata_config:
                st.session_state.metadata_config["document_type_prompts"] = {}
            
            # Display prompt for each document type
            for doc_type in document_types:
                # Get current prompt for document type
                current_prompt = st.session_state.metadata_config["document_type_prompts"].get(
                    doc_type, st.session_state.metadata_config["freeform_prompt"]
                )
                
                # Display prompt input
                doc_type_prompt = st.text_area(
                    f"Prompt for {doc_type}",
                    value=current_prompt,
                    height=100,
                    key=f"prompt_{doc_type.replace(' ', '_').lower()}",
                    help=f"Customize the prompt for {doc_type} documents"
                )
                
                # Update prompt in session state
                st.session_state.metadata_config["document_type_prompts"][doc_type] = doc_type_prompt
    
    # Structured extraction configuration
    else:
        st.subheader("Structured Extraction Configuration")
        
        # Check if metadata templates are available
        if not hasattr(st.session_state, "metadata_templates") or not st.session_state.metadata_templates:
            st.warning("No metadata templates available. Please refresh templates in the sidebar.")
            return
        
        # Get available templates
        templates = st.session_state.metadata_templates
        
        # Create template options
        template_options = [("", "None - Use custom fields")]
        for template_id, template in templates.items():
            template_options.append((template_id, template["displayName"]))
        
        # Template selection
        st.write("#### Select Metadata Template")
        
        # Document type template mapping
        if has_categorization:
            st.subheader("Document Type Template Mapping")
            st.info("You can map each document type to a specific metadata template.")
            
            # Get unique document types
            document_types = set()
            for file_id, result in st.session_state.document_categorization["results"].items():
                document_types.add(result["document_type"])
            
            # Initialize document type to template mapping if not exists
            if not hasattr(st.session_state, "document_type_to_template"):
                from modules.metadata_template_retrieval import initialize_template_state
                initialize_template_state()
            
            # Display template selection for each document type
            for doc_type in document_types:
                # Get current template for document type
                current_template_id = st.session_state.document_type_to_template.get(doc_type)
                
                # Find index of current template in options
                selected_index = 0
                for i, (template_id, _) in enumerate(template_options):
                    if template_id == current_template_id:
                        selected_index = i
                        break
                
                # Display template selection
                selected_template = st.selectbox(
                    f"Template for {doc_type}",
                    options=[option[1] for option in template_options],
                    index=selected_index,
                    key=f"template_{doc_type.replace(' ', '_').lower()}",
                    help=f"Select a metadata template for {doc_type} documents"
                )
                
                # Find template ID from selected name
                selected_template_id = ""
                for template_id, template_name in template_options:
                    if template_name == selected_template:
                        selected_template_id = template_id
                        break
                
                # Update template in session state
                st.session_state.document_type_to_template[doc_type] = selected_template_id
        
        # General template selection (for all files)
        selected_template_name = st.selectbox(
            "Select a metadata template",
            options=[option[1] for option in template_options],
            index=0,
            key="template_selectbox",
            help="Select a metadata template to use for structured extraction"
        )
        
        # Find template ID from selected name
        selected_template_id = ""
        for template_id, template_name in template_options:
            if template_name == selected_template_name:
                selected_template_id = template_id
                break
        
        # Update template ID in session state
        st.session_state.metadata_config["template_id"] = selected_template_id
        st.session_state.metadata_config["use_template"] = (selected_template_id != "")
        
        # Display template details if selected
        if selected_template_id:
            template = templates[selected_template_id]
            
            st.write("#### Template Details")
            st.write(f"**Name:** {template['displayName']}")
            st.write(f"**ID:** {template['id']}")
            
            # Display fields
            st.write("**Fields:**")
            for field in template["fields"]:
                st.write(f"- {field['displayName']} ({field['type']})")
        
        # Custom fields if no template selected
        else:
            st.write("#### Custom Fields")
            st.write("Define custom fields for structured extraction")
            
            # Initialize custom fields if not exists
            if "custom_fields" not in st.session_state.metadata_config:
                st.session_state.metadata_config["custom_fields"] = []
            
            # Display existing custom fields
            for i, field in enumerate(st.session_state.metadata_config["custom_fields"]):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    field_name = st.text_input(
                        "Field Name",
                        value=field["name"],
                        key=f"field_name_{i}",
                        help="Name of the custom field"
                    )
                
                with col2:
                    field_type = st.selectbox(
                        "Field Type",
                        options=["string", "number", "date", "enum"],
                        index=["string", "number", "date", "enum"].index(field["type"]),
                        key=f"field_type_{i}",
                        help="Type of the custom field"
                    )
                
                with col3:
                    if st.button("Remove", key=f"remove_field_{i}"):
                        st.session_state.metadata_config["custom_fields"].pop(i)
                        st.rerun()
                
                # Update field in session state
                st.session_state.metadata_config["custom_fields"][i]["name"] = field_name
                st.session_state.metadata_config["custom_fields"][i]["type"] = field_type
            
            # Add new field button
            if st.button("Add Field", key="add_field_button"):
                st.session_state.metadata_config["custom_fields"].append({
                    "name": f"Field {len(st.session_state.metadata_config['custom_fields']) + 1}",
                    "type": "string"
                })
                st.rerun()
    
    # AI model selection
    st.subheader("AI Model Selection")

    # Updated list of models with descriptions - FILTERED FOR /ai/extract_structured
    # Based on API error response (May 5, 2025) and Box Docs
    # Allowed values from error: ["azure__openai__gpt_4o_mini", "azure__openai__gpt_4_1", "azure__openai__gpt_4_1_mini", "google__gemini_1_5_pro_001", "google__gemini_1_5_flash_001", "google__gemini_2_0_flash_001", "google__gemini_2_0_flash_lite_preview", "aws__claude_3_haiku", "aws__claude_3_sonnet", "aws__claude_3_5_sonnet", "aws__claude_3_7_sonnet", "aws__titan_text_lite", "ibm__llama_3_2_90b_vision_instruct", "ibm__llama_4_scout"]
    # Note: ibm__llama_3_2_90b_vision_instruct was not in original docs list, adding based on error.
    # Note: google__gemini_2_0_flash_lite_preview is listed as default in docs, keeping.
    all_models_with_desc = {
        "google__gemini_2_0_flash_lite_preview": "Google Gemini 2.0 Flash Lite: Lightweight multimodal model (Default for Box AI Extract) (Preview)",
        "azure__openai__gpt_4o_mini": "Azure OpenAI GPT-4o Mini: Lightweight multimodal model",
        "azure__openai__gpt_4o": "Azure OpenAI GPT-4o: Highly efficient multimodal model for complex tasks", # Not in allowedValues
        "azure__openai__gpt_4_1_mini": "Azure OpenAI GPT-4.1 Mini: Lightweight multimodal model (Default for some Box AI features)",
        "azure__openai__gpt_4_1": "Azure OpenAI GPT-4.1: Highly efficient multimodal model for complex tasks",
        "azure__openai__gpt_o3": "Azure OpenAI GPT o3: Highly efficient multimodal model for complex tasks", # Not in allowedValues
        "azure__openai__gpt_o4-mini": "Azure OpenAI GPT o4-mini: Highly efficient multimodal model for complex tasks", # Not in allowedValues
        "google__gemini_2_5_pro_preview": "Google Gemini 2.5 Pro: Optimal for high-volume, high-frequency tasks (Preview)", # Not in allowedValues
        "google__gemini_2_5_flash_preview": "Google Gemini 2.5 Flash: Optimal for high-volume, high-frequency tasks (Preview)", # Not in allowedValues
        "google__gemini_2_0_flash_001": "Google Gemini 2.0 Flash: Optimal for high-volume, high-frequency tasks",
        "google__gemini_1_5_flash_001": "Google Gemini 1.5 Flash: High volume tasks & latency-sensitive applications",
        "google__gemini_1_5_pro_001": "Google Gemini 1.5 Pro: Foundation model for various multimodal tasks",
        "aws__claude_3_haiku": "AWS Claude 3 Haiku: Tailored for various language tasks",
        "aws__claude_3_sonnet": "AWS Claude 3 Sonnet: Advanced language tasks, comprehension & context handling",
        "aws__claude_3_5_sonnet": "AWS Claude 3.5 Sonnet: Enhanced language understanding and generation",
        "aws__claude_3_7_sonnet": "AWS Claude 3.7 Sonnet: Enhanced language understanding and generation",
        "aws__titan_text_lite": "AWS Titan Text Lite: Advanced language processing, extensive contexts",
        "ibm__llama_3_2_instruct": "IBM Llama 3.2 Instruct: Instruction-tuned text model for dialogue, retrieval, summarization", # Renamed in error log?
        "ibm__llama_3_2_90b_vision_instruct": "IBM Llama 3.2 90B Vision Instruct: Instruction-tuned vision model (From Error Log)", # Added from error log
        "ibm__llama_4_scout": "IBM Llama 4 Scout: Natively multimodal model for text and multimodal experiences",
        "xai__grok_3_beta": "xAI Grok 3: Excels at data extraction, coding, summarization (Beta)", # Not in allowedValues
        "xai__grok_3_mini_beta": "xAI Grok 3 Mini: Lightweight model for logic-based tasks (Beta)" # Not in allowedValues
    }

    # Filtered list based on API error response for /ai/extract_structured
    allowed_model_names = [
        "azure__openai__gpt_4o_mini", "azure__openai__gpt_4_1", "azure__openai__gpt_4_1_mini",
        "google__gemini_1_5_pro_001", "google__gemini_1_5_flash_001", "google__gemini_2_0_flash_001",
        "google__gemini_2_0_flash_lite_preview", "aws__claude_3_haiku", "aws__claude_3_sonnet",
        "aws__claude_3_5_sonnet", "aws__claude_3_7_sonnet", "aws__titan_text_lite",
        "ibm__llama_3_2_90b_vision_instruct", "ibm__llama_4_scout"
    ]

    # Create the filtered dictionary for the dropdown
    ai_models_with_desc = {name: all_models_with_desc.get(name, f"{name} (Description not found)")
                           for name in allowed_model_names if name in all_models_with_desc}

    # Add any models from allowed list that might have been missed in the initial dict
    for name in allowed_model_names:
        if name not in ai_models_with_desc:
             ai_models_with_desc[name] = f"{name} (Description not found)"
             logger.warning(f"Model 	{name}	 from allowed list was missing description, added placeholder.")

    # Get the list of model names (keys) from the filtered list
    ai_model_names = list(ai_models_with_desc.keys())

    # Get the list of descriptions (values) to display in the dropdown
    ai_model_options = list(ai_models_with_desc.values())

    # Find the index of the currently selected model's description
    current_model_name = st.session_state.metadata_config.get("ai_model", ai_model_names[0]) # Default to first if not set

    # Ensure the current model is actually in the allowed list
    if current_model_name not in ai_model_names:
        logger.warning(f"Previously selected model 	{current_model_name}	 is not allowed for extraction. Defaulting to 	{ai_model_names[0]}	.")
        current_model_name = ai_model_names[0]
        st.session_state.metadata_config["ai_model"] = current_model_name # Update session state

    try:
        # Find the description corresponding to the current model name
        current_model_desc = ai_models_with_desc.get(current_model_name, ai_model_options[0])
        selected_index = ai_model_options.index(current_model_desc)
    except (ValueError, KeyError):
        # Fallback if current model description not found (should be rare after filtering)
        logger.error(f"Error finding index for model 	{current_model_name}	. Defaulting to first model.")
        selected_index = 0
        current_model_name = ai_model_names[selected_index]
        st.session_state.metadata_config["ai_model"] = current_model_name # Update session state

    # Use descriptions in the selectbox options
    selected_model_desc = st.selectbox(
        "Select AI Model",
        options=ai_model_options,
        index=selected_index,
        key="ai_model_selectbox",
        help="Choose the AI model for metadata extraction. Only models supported by the extraction endpoint are listed."
    )

    # Find the model name (key) corresponding to the selected description
    selected_model_name = ""
    for name, desc in ai_models_with_desc.items():
        if desc == selected_model_desc:
            selected_model_name = name
            break

    # Update AI model name in session state
    st.session_state.metadata_config["ai_model"] = selected_model_name
    
    # Batch processing configuration
    st.subheader("Batch Processing Configuration")
    
    batch_size = st.slider(
        "Batch Size",
        min_value=1,
        max_value=10,
        value=st.session_state.metadata_config["batch_size"],
        step=1,
        key="batch_size_slider",
        help="Number of files to process in parallel"
    )
    
    # Update batch size in session state
    st.session_state.metadata_config["batch_size"] = batch_size
    
    # Continue button
    st.write("---")
    if st.button("Continue to Process Files", key="continue_to_process_button", use_container_width=True):
        st.session_state.current_page = "Process Files"
        st.rerun()

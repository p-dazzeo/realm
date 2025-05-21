"""
Main Streamlit application for REALM.
"""
import os
import json
import requests
from pathlib import Path
import streamlit as st
from typing import Dict, List, Any, Optional

from frontend.src.clients.gendoc import GenDocClient
from frontend.src.clients.rag import RAGClient

# Define service URLs
GENDOC_URL = os.getenv("GENDOC_URL", "http://localhost:8000")
RAG_URL = os.getenv("RAG_URL", "http://localhost:8001")

# Initialize clients
gendoc_client = GenDocClient(GENDOC_URL)
rag_client = RAGClient(RAG_URL)

# Set page config
st.set_page_config(
    page_title="REALM - Reverse Engineering Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None
if "project_files" not in st.session_state:
    st.session_state.project_files = []
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
if "doc_history" not in st.session_state:
    st.session_state.doc_history = []
if "rag_history" not in st.session_state:
    st.session_state.rag_history = []


def upload_project(file, project_id: str, description: str = None) -> Dict:
    """Upload project to both services."""
    # Upload to GenDoc service
    file.seek(0)  # Reset file pointer to beginning
    gendoc_response = gendoc_client.upload_project(project_id, file, description)
    
    # Reset file pointer for RAG service
    file.seek(0)  # Reset file pointer to beginning again
    rag_response = rag_client.upload_project(project_id, file, description, index_immediately=True)
    
    return {
        "gendoc": gendoc_response,
        "rag": rag_response
    }


def get_documentation(project_id: str, doc_type: str, file_path: Optional[str] = None, 
                     custom_prompt: Optional[str] = None, model_name: str = "gpt-4") -> Dict:
    """Get documentation from the GenDoc service."""
    return gendoc_client.generate_documentation(
        project_id=project_id,
        doc_type=doc_type,
        file_path=file_path,
        custom_prompt=custom_prompt,
        model_name=model_name
    )


def query_rag(project_id: str, query: str, file_paths: Optional[List[str]] = None, 
             model_name: str = "gpt-4") -> Dict:
    """Query the RAG service."""
    return rag_client.query_rag(
        project_id=project_id,
        query=query,
        file_paths=file_paths,
        model_name=model_name
    )


def display_header():
    """Display the application header."""
    col1, col2 = st.columns([1, 5])
    
    with col1:
        st.image("https://via.placeholder.com/150x150.png?text=REALM", width=100)
    
    with col2:
        st.title("REALM - Reverse Engineering Assistant")
        st.write("Generate comprehensive documentation for your code with AI assistance")


def display_project_upload():
    """Display the project upload section."""
    st.header("Upload Project")
    
    with st.form("upload_form"):
        project_id = st.text_input("Project ID", help="A unique identifier for your project")
        description = st.text_area("Description", help="Optional description of the project")
        uploaded_file = st.file_uploader("Upload ZIP file", type=["zip"], 
                                        help="Upload a ZIP file containing your code")
        
        submit_button = st.form_submit_button("Upload & Process")
        
        if submit_button and uploaded_file and project_id:
            with st.spinner("Uploading and processing project..."):
                try:
                    result = upload_project(uploaded_file, project_id, description)
                    st.session_state.current_project_id = project_id
                    st.success(f"Project uploaded successfully! Project ID: {project_id}")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error uploading project: {str(e)}")


def display_documentation_generator():
    """Display the documentation generator section."""
    st.header("Documentation Generator")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        doc_type = st.selectbox(
            "Documentation Type",
            ["overview", "architecture", "component", "function", "api", "custom"],
            help="Select the type of documentation to generate"
        )
        
        model_name = st.selectbox(
            "Model",
            ["gpt-4o", "o4-mini"],
            index=0,
            help="Select the LLM model to use"
        )
    
    with col2:
        file_specific = st.checkbox("File-specific documentation", 
                                  help="Generate documentation for a specific file")
        
        if file_specific:
            selected_file = st.selectbox("Select File", st.session_state.project_files)
        else:
            selected_file = None
    
    custom_prompt = None
    if doc_type == "custom":
        custom_prompt = st.text_area("Custom Prompt", 
                                    help="Enter a custom prompt for the documentation generator")
    
    if st.button("Generate Documentation"):
        with st.spinner("Generating documentation..."):
            try:
                response = get_documentation(
                    st.session_state.current_project_id,
                    doc_type,
                    selected_file,
                    custom_prompt,
                    model_name
                )
                
                # Add to history
                st.session_state.doc_history.append({
                    "doc_type": doc_type,
                    "file_path": selected_file,
                    "documentation": response["documentation"],
                    "model_name": model_name
                })
                
                st.success("Documentation generated successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error generating documentation: {str(e)}")


def display_rag_interface():
    """Display the RAG interface section."""
    st.header("Ask Questions About Your Code")
    
    with st.form("rag_form"):
        query = st.text_area("Your Question", help="Ask a question about the codebase")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            model_name = st.selectbox(
                "Model",
                ["gpt-4o", "o4-mini"],
                index=0,
                help="Select the LLM model to use",
                key="rag_model"
            )
        
        with col2:
            file_specific = st.checkbox("Limit to specific files", 
                                      help="Limit search to specific files")
            
            if file_specific:
                selected_files = st.multiselect("Select Files", st.session_state.project_files)
            else:
                selected_files = None
        
        submit_button = st.form_submit_button("Ask Question")
        
        if submit_button and query:
            with st.spinner("Processing your question..."):
                try:
                    response = query_rag(
                        st.session_state.current_project_id,
                        query,
                        selected_files,
                        model_name
                    )
                    
                    # Add to history
                    st.session_state.rag_history.append({
                        "query": query,
                        "answer": response["answer"],
                        "sources": response["sources"],
                        "model_name": model_name
                    })
                    
                    st.success("Question answered!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error processing question: {str(e)}")


def display_documentation_history():
    """Display documentation history."""
    if not st.session_state.doc_history:
        st.info("No documentation has been generated yet.")
        return
    
    for i, item in enumerate(reversed(st.session_state.doc_history)):
        with st.expander(f"{item['doc_type'].title()} Documentation - {item['file_path'] or 'Project Overview'}", expanded=(i == 0)):
            st.markdown(f"**Model:** {item['model_name']}")
            st.markdown(item["documentation"])


def display_rag_history():
    """Display RAG history."""
    if not st.session_state.rag_history:
        st.info("No questions have been asked yet.")
        return
    
    for i, item in enumerate(reversed(st.session_state.rag_history)):
        with st.expander(f"Q: {item['query']}", expanded=(i == 0)):
            st.markdown(f"**Model:** {item['model_name']}")
            st.markdown(f"**Answer:**\n{item['answer']}")
            
            st.markdown("**Sources:**")
            for j, source in enumerate(item["sources"]):
                with st.expander(f"Source {j+1}: {source['metadata']['file_path']}"):
                    st.code(source["content"], language="python")


def main():
    """Main application function."""
    display_header()
    
    # Sidebar
    st.sidebar.title("Navigation")
    
    if st.session_state.current_project_id:
        st.sidebar.success(f"Current Project: {st.session_state.current_project_id}")
        
        # Get project files using the GenDoc client
        if not st.session_state.project_files:
            st.session_state.project_files = gendoc_client.list_project_files(st.session_state.current_project_id)
        
        page = st.sidebar.radio(
            "Select Page",
            ["Upload New Project", "Generate Documentation", "Ask Questions", "Documentation History", "Questions History"]
        )
        
        if page == "Upload New Project":
            display_project_upload()
        elif page == "Generate Documentation":
            display_documentation_generator()
        elif page == "Ask Questions":
            display_rag_interface()
        elif page == "Documentation History":
            st.header("Documentation History")
            display_documentation_history()
        elif page == "Questions History":
            st.header("Questions History")
            display_rag_history()
    else:
        display_project_upload()


if __name__ == "__main__":
    main() 
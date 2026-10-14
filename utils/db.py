import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    """Initializes and caches the Supabase database connection."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def upload_file_to_storage(client: Client, bucket_name: str, file_bytes: bytes, file_path: str, content_type: str = "application/pdf") -> str:
    """Uploads a PDF or HTML resource to Supabase Storage and returns the public URL."""
    try:
        client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        public_url = client.storage.from_(bucket_name).get_public_url(file_path)
        return public_url
    except Exception as e:
        st.error(f"Storage Upload Error: {e}")
        return ""
import streamlit as st
import requests
import json
import os
import time

# Configure page layout and aesthetics
st.set_page_config(
    page_title="AI Agent OS Workspace",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL mapping (internal container communication)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")

# Initialize session states
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "active_conv_id" not in st.session_state:
    st.session_state.active_conv_id = None
if "refresh_trigger" not in st.session_state:
    st.session_state.refresh_trigger = 0

def get_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

# ── Auth helper functions ─────────────────────────────────────────────
def login(email, password):
    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            data = res.json()
            st.session_state.token = data["access_token"]
            fetch_user_profile()
            st.session_state.refresh_trigger += 1
            return True, "success"
        elif res.status_code == 403:
            return False, "verification_required"
        else:
            return False, "invalid_credentials"
    except Exception as e:
        return False, f"Connection error: {e}"

def signup(email, password, name):
    try:
        res = requests.post(f"{BACKEND_URL}/auth/signup", json={"email": email, "password": password, "full_name": name})
        if res.status_code == 201:
            return True, "success"
        else:
            try:
                detail = res.json().get("detail", "Signup failed.")
            except Exception:
                detail = "Signup failed."
            return False, detail
    except Exception as e:
        return False, f"Connection error: {e}"

def fetch_user_profile():
    if not st.session_state.token:
        return
    try:
        res = requests.get(f"{BACKEND_URL}/auth/me", headers=get_headers())
        if res.status_code == 200:
            st.session_state.user = res.json()
        else:
            logout()
    except Exception:
        logout()

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.active_conv_id = None
    st.session_state.refresh_trigger += 1

# ── SSE Chat stream reader ──────────────────────────────────────────
def message_stream_generator(conv_id, content):
    url = f"{BACKEND_URL}/chat/conversations/{conv_id}/messages"
    payload = {"content": content}
    
    with requests.post(url, json=payload, headers=get_headers(), stream=True) as r:
        if r.status_code != 200:
            yield f"❌ Error sending message (HTTP {r.status_code})"
            return
            
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    try:
                        data = json.loads(decoded_line[6:])
                        if data.get("type") == "token":
                            yield data.get("content", "")
                        elif data.get("type") == "error":
                            yield f"\n❌ Error: {data.get('detail', '')}"
                    except Exception:
                        pass

# ── Unauthenticated view ─────────────────────────────────────────────
if not st.session_state.user:
    st.title("🤖 AI OS Workspace Portal")
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            if submitted:
                success, code = login(email, password)
                if success:
                    st.success("Signed in successfully!")
                    st.rerun()
                elif code == "verification_required":
                    st.warning("⚠️ Email not verified. Please verify your email first (link printed in console/logs).")
                else:
                    st.error("Invalid email or password.")
                    
    with tab2:
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            password = st.text_input("Password (min 8 chars)", type="password")
            submitted = st.form_submit_button("Create Account")
            if submitted:
                if len(password) < 8:
                    st.error("Password must be at least 8 characters long.")
                else:
                    success, detail = signup(email, password, name)
                    if success:
                        st.success("🎉 Account created successfully! Please verify your email using the link printed in the console logs before signing in.")
                    else:
                        st.error(f"Signup failed: {detail}")

# ── Authenticated Workspace ──────────────────────────────────────────
else:
    # Sidebar layout
    with st.sidebar:
        st.markdown(f"### 🤖 AI OS Workspace")
        st.markdown(f"Logged in as **{st.session_state.user.get('full_name')}**")
        st.markdown("🚀 *Standard Multi-User Workspace*")
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            logout()
            st.rerun()

    # Main dashboard view
    st.markdown("## ⚙️ AI OS Dashboard")
    tab_chat, tab_docs, tab_workflows, tab_repos = st.tabs([
        "💬 Multi-Agent Chat", 
        "📂 RAG Knowledge Base", 
        "⚡ Automation Workflows", 
        "📦 Connected Repositories"
    ])
    
    # ──── Tab 1: Chat Workspace ────
    with tab_chat:
        col1, col2 = st.columns([1, 3])
        
        # Conversation manager
        with col1:
            st.markdown("#### Threads")
            if st.button("➕ New Chat Thread", use_container_width=True):
                # Create conversation session
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/chat/conversations", 
                        json={"title": f"Chat {time.strftime('%H:%M')}", "agent_type": "general"},
                        headers=get_headers()
                    )
                    if res.status_code == 201:
                        st.session_state.active_conv_id = res.json()["id"]
                except Exception as e:
                    st.error(f"Error creating thread: {e}")
            
            # List existing chats
            try:
                res = requests.get(f"{BACKEND_URL}/chat/conversations", headers=get_headers())
                if res.status_code == 200:
                    convs = res.json()
                    for c in convs:
                        btn_label = f"💬 {c['title']}"
                        is_active = (st.session_state.active_conv_id == c["id"])
                        if st.button(btn_label, key=f"conv_{c['id']}", use_container_width=True, type="secondary" if not is_active else "primary"):
                            st.session_state.active_conv_id = c["id"]
                            st.rerun()
            except Exception:
                st.write("Could not retrieve threads.")

        # Chat Window
        with col2:
            if not st.session_state.active_conv_id:
                st.info("Select or create a chat thread from the left pane to begin.")
            else:
                # Load conversation details & history
                conv_id = st.session_state.active_conv_id
                
                # Fetch past messages
                messages = []
                try:
                    res = requests.get(f"{BACKEND_URL}/chat/conversations/{conv_id}/messages", headers=get_headers())
                    if res.status_code == 200:
                        messages = res.json()
                except Exception:
                    pass
                
                # Show messages
                for msg in messages:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])
                        if msg.get("citations"):
                            with st.expander("📚 View Citations"):
                                for cit in msg["citations"]:
                                    st.markdown(f"- **{cit.get('filename', 'Unknown')}** (Page/Chunk: {cit.get('chunk_index', cit.get('page', 0))})")
                                    if cit.get("content"):
                                        st.caption(cit["content"])
                
                # Accept chat inputs
                if prompt := st.chat_input("Ask the Multi-Agent OS..."):
                    # Render user input
                    with st.chat_message("user"):
                        st.write(prompt)
                    
                    # Call streaming backend
                    with st.chat_message("assistant"):
                        response_placeholder = st.empty()
                        full_response = ""
                        for chunk in message_stream_generator(conv_id, prompt):
                            full_response += chunk
                            response_placeholder.write(full_response)
                        
                        # Reload message history once streamed
                        time.sleep(0.5)
                        st.rerun()

    # ──── Tab 2: RAG Documents ────
    with tab_docs:
        st.markdown("#### Knowledge Base Files")
        
        # Document Uploader form
        uploaded_file = st.file_uploader("Upload document for RAG indexing", type=["txt", "pdf", "docx", "md"])
        if uploaded_file:
            if st.button("📤 Index Uploaded File"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    res = requests.post(f"{BACKEND_URL}/documents/upload", files=files, headers=get_headers())
                    
                    if res.status_code == 202:
                        st.success(f"File '{uploaded_file.name}' accepted. Ingestion running in background.")
                        time.sleep(1.0)
                        st.rerun()
                    else:
                        st.error(f"In-app upload error (HTTP {res.status_code})")
                except Exception as e:
                    st.error(f"Upload failed: {e}")
        
        # List Documents
        try:
            res = requests.get(f"{BACKEND_URL}/documents", headers=get_headers())
            if res.status_code == 200:
                docs = res.json()
                if not docs:
                    st.write("No documents indexed yet.")
                else:
                    for d in docs:
                        st.markdown(f"- **{d['filename']}** | Status: `{d['status']}` | Indexed: {d['created_at'][:16]}")
        except Exception:
            st.write("Could not retrieve documents.")

    # ──── Tab 3: Workflows ────
    with tab_workflows:
        st.markdown("#### Automated Workflow Chains")
        
        # Create workflow inline
        with st.expander("➕ Define New Workflow"):
            with st.form("new_wf_form"):
                wf_name = st.text_input("Workflow Name")
                submit_wf = st.form_submit_button("Create Workflow")
                if submit_wf and wf_name.strip():
                    try:
                        # Define default steps so it actually runs and does something
                        default_steps = [
                            {"agent_type": "planning", "input_data": {"task": f"Decompose plan for {wf_name}"}},
                            {"agent_type": "research", "input_data": {"query": f"Research context for {wf_name}"}},
                            {"agent_type": "code", "input_data": {"action": f"Review repository code for {wf_name}"}}
                        ]
                        res = requests.post(f"{BACKEND_URL}/workflows/", json={"name": wf_name, "steps": default_steps}, headers=get_headers())
                        if res.status_code == 201:
                            st.success(f"Workflow '{wf_name}' created successfully with default steps.")
                            time.sleep(1.0)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
                        
        # List and Execute Workflows
        try:
            res = requests.get(f"{BACKEND_URL}/workflows", headers=get_headers())
            if res.status_code == 200:
                wfs = res.json()
                if not wfs:
                    st.write("No workflows created yet.")
                else:
                    for wf in wfs:
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.markdown(f"### ⚡ {wf['name']} (Status: `{wf['status']}`)")
                        with col_b:
                            if st.button("⚡ Run Workflow", key=f"run_wf_{wf['id']}"):
                                try:
                                    run_res = requests.post(f"{BACKEND_URL}/workflows/{wf['id']}/execute", headers=get_headers())
                                    if run_res.status_code == 202:
                                        st.success("Workflow execution queued in Celery worker.")
                                        time.sleep(1.5)
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Run failed: {e}")
                        
                        # Render steps inside an expander
                        if "steps" in wf and wf["steps"]:
                            with st.expander("📄 View Step Details", expanded=True):
                                for step in wf["steps"]:
                                    status_emoji = "⏳"
                                    if step["status"] == "completed":
                                        status_emoji = "✅"
                                    elif step["status"] == "running":
                                        status_emoji = "⚡"
                                    elif step["status"] == "failed":
                                        status_emoji = "❌"
                                    st.markdown(f"{status_emoji} **Step {step['step_order'] + 1}**: `{step['agent_type'].capitalize()} Agent` | Status: `{step['status']}`")
                                    if step["output_data"]:
                                        st.json(step["output_data"])
                        st.markdown("---")
        except Exception:
            st.write("Could not retrieve workflows.")

    # ──── Tab 4: Repositories ────
    with tab_repos:
        st.markdown("#### Connected Codebases")
        
        # Connect repo form
        with st.expander("🔌 Connect Repository"):
            with st.form("new_repo_form"):
                repo_url = st.text_input("GitHub URL")
                branch = st.text_input("Branch Name", value="main")
                submit_repo = st.form_submit_button("Analyze Codebase")
                if submit_repo and repo_url.strip():
                    try:
                        res = requests.post(f"{BACKEND_URL}/repositories/analyze", json={"repo_url": repo_url, "branch": branch}, headers=get_headers())
                        if res.status_code == 202:
                            st.success("Codebase connected. Celery analysis dispatched.")
                            time.sleep(1.0)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
                        
        # List Connected Repos
        try:
            res = requests.get(f"{BACKEND_URL}/repositories", headers=get_headers())
            if res.status_code == 200:
                repos = res.json()
                if not repos:
                    st.write("No codebases connected yet.")
                else:
                    for r in repos:
                        st.markdown(f"- **{r['name']}** | Status: `{r['status']}` | Linked: {r['created_at'][:10]}")
        except Exception:
            st.write("Could not retrieve repositories.")

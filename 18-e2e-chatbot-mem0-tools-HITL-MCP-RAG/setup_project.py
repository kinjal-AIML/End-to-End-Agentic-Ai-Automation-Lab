import os

def create_project_structure():
    # The root directory name
    root_dir = "chatbot_backend"

    # Define the directory structure
    directories = [
        "app",
        "app/api",
        "app/core",
        "app/models",
        "app/services",
        "app/utils",
        "tests",
    ]

    # Define the files to create
    files = [
        ".env",
        "requirements.txt",
        "main.py",
        "app/__init__.py",
        "app/api/__init__.py",
        "app/api/chat.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/models/__init__.py",
        "app/models/schemas.py",
        "app/models/state.py",
        "app/services/__init__.py",
        "app/services/nodes.py",
        "app/services/graph_builder.py",
        "app/utils/__init__.py",
        "app/utils/prompts.py",
        "tests/__init__.py",
        "tests/test_api.py",
    ]

    print(f"🚀 Starting project generation for: {root_dir}...")

    # 1. Create the Root Directory
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
        print(f"📁 Created root directory: {root_dir}/")
    else:
        print(f"ℹ️  Root directory {root_dir}/ already exists.")

    # 2. Create Sub-directories
    for folder in directories:
        dir_path = os.path.join(root_dir, folder)
        os.makedirs(dir_path, exist_ok=True)
        print(f"   📂 Created directory: {folder}/")

    # 3. Create Files
    for file in files:
        file_path = os.path.join(root_dir, file)
        
        # Create an empty file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                pass  # Create empty file
            print(f"   kB Created file:      {file}")
        else:
            print(f"   ℹ️  File already exists: {file}")

    print("\n✅ Project structure created successfully!")
    print(f"👉 To get started: cd {root_dir}")

if __name__ == "__main__":
    create_project_structure()
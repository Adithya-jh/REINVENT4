import gradio as gr
import subprocess
import tempfile
import shutil
import os

# Determine the path to the REINVENT4 repository root
def get_repo_root():
    # Assumes this script lives in the repo root or a subdirectory
    return os.path.abspath(os.path.dirname(__file__))


def run_reinvent(toml_file_path):
    repo_root = get_repo_root()
    # Create a temporary working directory for this run
    workdir = tempfile.mkdtemp(prefix="reinvent_run_")
    try:
        # Copy the TOML into the workdir
        basename = os.path.basename(toml_file_path)
        toml_dest = os.path.join(workdir, basename)
        shutil.copy(toml_file_path, toml_dest)

        # Copy the priors directory so REINVENT can find its models
        priors_src = os.path.join(repo_root, "priors")
        priors_dest = os.path.join(workdir, "priors")
        if os.path.isdir(priors_src):
            shutil.copytree(priors_src, priors_dest)

        # Run REINVENT in CPU mode
        cmd = ["reinvent", "-d", "cpu", "-l", "sampling.log", toml_dest]
        proc = subprocess.run(cmd, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Paths for expected outputs
        csv_path = os.path.join(workdir, "sampling.csv")
        json_path = os.path.join(workdir, "sampling.json")
        log_path = os.path.join(workdir, "sampling.log")

        # Gather outputs
        out_csv = csv_path if os.path.exists(csv_path) else None
        out_json = json_path if os.path.exists(json_path) else None
        out_log = log_path if os.path.exists(log_path) else None
        output_text = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
        return out_csv, out_json, out_log, output_text
    finally:
        # Keep workdir so Gradio can serve files
        pass


def build_interface():
    iface = gr.Interface(
        fn=run_reinvent,
        inputs=gr.File(label="Upload your TOML config file (.toml)", type="filepath"),
        outputs=[
            gr.File(label="Download sampling.csv", type="filepath"),
            gr.File(label="Download sampling.json", type="filepath"),
            gr.File(label="Download sampling.log", type="filepath"),
            gr.Textbox(label="REINVENT stdout/stderr")
        ],
        title="REINVENT4 Web Interface",
        description="Upload a REINVENT4 TOML configuration, run on CPU, and retrieve CSV/JSON/log outputs.",
        flagging_mode='never'
    )
    return iface

if __name__ == "__main__":
    iface = build_interface()
    iface.launch(share=True)

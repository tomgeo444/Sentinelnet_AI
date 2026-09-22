#!/usr/bin/env python3
"""Generate a comprehensive Beginner's Guide PDF for SentinelNet AI."""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

OUTPUT_PATH = "/home/othniel/sentinel/docs/SentinelNet_AI_Beginner_Guide.pdf"


class BeginnerGuidePDF(FPDF):
    """Custom PDF class with header/footer for the beginner guide."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self._is_cover = True

    def header(self):
        if self._is_cover:
            return
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "SentinelNet AI  --  Beginner's Complete Guide",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self):
        if self._is_cover:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}",
                  new_x=XPos.RIGHT, new_y=YPos.TOP, align="C")
        self.set_text_color(0, 0, 0)


def safe(text):
    """Strip non-ASCII characters to avoid fpdf2 encoding errors."""
    return text.encode("ascii", "replace").decode("ascii").replace("?", "-")


def page_check(pdf, needed=30):
    if pdf.get_y() > 260 - needed:
        pdf.add_page()


def add_chapter(pdf, num, title):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(0, 70, 140)
    pdf.cell(0, 12, safe(f"Chapter {num}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 18)
    pdf.multi_cell(0, 10, safe(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 70, 140)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(8)


def add_section(pdf, title):
    page_check(pdf, 20)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 50, 100)
    pdf.multi_cell(0, 8, safe(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)


def add_subsection(pdf, title):
    page_check(pdf, 15)
    pdf.set_font("Helvetica", "BI", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 7, safe(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def add_para(pdf, text):
    page_check(pdf, 12)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)


def add_bold_para(pdf, text):
    page_check(pdf, 12)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 6, safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(3)


def add_bullet(pdf, text, indent=10):
    page_check(pdf, 10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_x(pdf.l_margin + indent)
    w = pdf.w - pdf.l_margin - pdf.r_margin - indent
    pdf.multi_cell(w, 6, safe(f"  *  {text}"),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def add_numbered(pdf, num, text, indent=10):
    page_check(pdf, 10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_x(pdf.l_margin + indent)
    w = pdf.w - pdf.l_margin - pdf.r_margin - indent
    pdf.multi_cell(w, 6, safe(f"  {num}. {text}"),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def add_code(pdf, text):
    page_check(pdf, 20)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Courier", "", 10)
    y_start = pdf.get_y()
    pdf.multi_cell(0, 5, safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                   fill=True)
    pdf.ln(4)


def add_note(pdf, text):
    page_check(pdf, 15)
    pdf.set_fill_color(255, 255, 220)
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 6, safe(f"NOTE: {text}"),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.ln(4)


def add_tip(pdf, text):
    page_check(pdf, 15)
    pdf.set_fill_color(220, 255, 220)
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 6, safe(f"TIP: {text}"),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.ln(4)


def add_warning(pdf, text):
    page_check(pdf, 15)
    pdf.set_fill_color(255, 230, 230)
    pdf.set_font("Helvetica", "B", 10)
    pdf.multi_cell(0, 6, safe(f"WARNING: {text}"),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.ln(4)


def add_simple_table(pdf, headers, rows, col_widths=None):
    """Draw a simple bordered table."""
    page_check(pdf, 10 + 8 * len(rows))
    if col_widths is None:
        w = 190 / len(headers)
        col_widths = [w] * len(headers)
    # Header row
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(0, 70, 140)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, safe(h), border=1, fill=True,
                 new_x=XPos.RIGHT, new_y=YPos.TOP, align="C")
    pdf.ln()
    # Data rows
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    for ri, row in enumerate(rows):
        pdf.set_fill_color(245, 245, 245) if ri % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        for i, val in enumerate(row):
            pdf.cell(col_widths[i], 7, safe(str(val)), border=1, fill=True,
                     new_x=XPos.RIGHT, new_y=YPos.TOP, align="C")
        pdf.ln()
    pdf.ln(5)


def generate():
    pdf = BeginnerGuidePDF()

    # ────────────────────── COVER PAGE ──────────────────────
    pdf.add_page()
    pdf._is_cover = True

    # Blue top bar
    pdf.set_fill_color(0, 70, 140)
    pdf.rect(0, 0, 210, 60, "F")

    pdf.set_font("Helvetica", "B", 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(18)
    pdf.cell(0, 18, "SentinelNet AI", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, safe("Real-Time AI Network Intrusion Detection System"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    pdf.set_text_color(0, 0, 0)
    pdf.ln(40)

    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(0, 14, "Beginner's Complete Guide", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 16)
    pdf.multi_cell(0, 8, safe(
        "Everything you need to know to install, run, and understand\n"
        "the SentinelNet AI intrusion detection system.\n"
        "No prior experience required."
    ), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    pdf.ln(30)
    pdf.set_draw_color(0, 70, 140)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("Helvetica", "I", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Version 1.0  --  September 2026",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.cell(0, 8, "Easy step-by-step guide for beginners",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_text_color(0, 0, 0)

    # ────────────────────── TABLE OF CONTENTS ──────────────────────
    pdf._is_cover = False
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 70, 140)
    pdf.cell(0, 14, "Table of Contents", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    toc = [
        ("Chapter 1", "What is SentinelNet AI?"),
        ("Chapter 2", "How Does It Work?"),
        ("Chapter 3", "What You Need (Prerequisites)"),
        ("Chapter 4", "Installation Step-by-Step"),
        ("Chapter 5", "Using the Dashboard"),
        ("Chapter 6", "Running the Live Demo"),
        ("Chapter 7", "Understanding the Results"),
        ("Chapter 8", "Project File Structure"),
        ("Chapter 9", "Troubleshooting Common Issues"),
        ("Chapter 10", "Frequently Asked Questions"),
    ]
    for ch, title in toc:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(30, 8, safe(ch), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 13)
        pdf.cell(0, 8, safe(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    # ═══════════════════ CHAPTER 1 ═══════════════════
    add_chapter(pdf, 1, "What is SentinelNet AI?")

    add_section(pdf, "What is Network Security?")
    add_para(pdf,
        "Imagine your home has doors, windows, and a fence. You lock your doors "
        "at night so strangers cannot walk in. Network security works the same way "
        "but for computers. Every time your computer connects to the internet, data "
        "flows in and out through 'doors' called ports. Network security makes sure "
        "that only the right data goes through the right doors, and that no one "
        "sneaks in uninvited.")
    add_para(pdf,
        "Just like a house can be broken into, a computer network can be attacked. "
        "Hackers might try to steal your passwords, take control of your computer, "
        "or crash your services by flooding them with garbage data. That is why we "
        "need tools that watch over the network 24/7.")

    add_section(pdf, "What is an Intrusion Detection System (IDS)?")
    add_para(pdf,
        "An Intrusion Detection System is like a security guard sitting in a control "
        "room, watching all the security camera feeds at once. The guard does not "
        "physically block anyone from entering, but the moment they spot something "
        "suspicious -- someone trying to pick a lock, someone running through the "
        "parking lot at 3 AM -- they sound the alarm.")
    add_para(pdf,
        "In computer terms, an IDS watches all the network traffic flowing through "
        "your system. When it sees something that looks like an attack, it creates "
        "an alert so that a human (or an automated system) can respond.")
    add_para(pdf,
        "There are two main types of IDS: (a) Signature-based, which looks for known "
        "attack patterns (like a fingerprint database for criminals), and (b) Anomaly-"
        "based, which learns what 'normal' looks like and flags anything unusual. "
        "SentinelNet AI uses the anomaly-based approach powered by Deep Learning.")

    add_section(pdf, "What Makes SentinelNet AI Special?")
    add_para(pdf,
        "Traditional IDS tools like Snort or Suricata rely on a big list of rules "
        "written by human experts. If a brand-new attack appears that is not in the "
        "rule list, these tools will miss it completely.")
    add_para(pdf,
        "SentinelNet AI is different. It uses a Deep Learning neural network -- a "
        "type of artificial intelligence that can learn patterns from data. Instead "
        "of matching rules, SentinelNet has studied 20,000 examples of network "
        "conversations (both normal and malicious). It has learned the mathematical "
        "patterns that distinguish safe traffic from attacks. This means it can even "
        "catch attack variations it has never seen before, as long as they share "
        "statistical similarities with known attacks.")
    add_para(pdf,
        "The key features that make SentinelNet AI stand out:")
    add_bullet(pdf, "Real-time analysis: It watches traffic live, not after the fact.")
    add_bullet(pdf, "Deep Learning AI: Uses a 1D-CNN neural network for classification.")
    add_bullet(pdf, "Beautiful dashboard: A dark-themed SOC dashboard shows everything visually.")
    add_bullet(pdf, "99.97% accuracy: Near-perfect detection on benchmark data.")
    add_bullet(pdf, "Safe demo mode: Generate fake attacks to see the system in action.")
    add_bullet(pdf, "No GPU needed: Runs on any laptop with a CPU.")

    add_section(pdf, "What Can It Detect?")
    add_para(pdf, "SentinelNet AI classifies network traffic into 5 categories:")

    add_simple_table(pdf,
        ["Category", "Description", "Danger Level"],
        [
            ["BENIGN", "Normal, safe traffic", "None"],
            ["Bot / Infiltration", "Automated malware activity", "High"],
            ["Brute Force", "Repeated password guessing", "High"],
            ["DoS / DDoS", "Flooding to crash services", "Critical"],
            ["Port Scan", "Probing for vulnerabilities", "Medium"],
        ],
        [40, 95, 55])

    add_section(pdf, "Real-World Analogy")
    add_para(pdf,
        "Think of SentinelNet AI as a smart security camera system for your network. "
        "Ordinary cameras just record video. A smart camera system uses AI to "
        "understand what it sees -- it can tell the difference between a delivery "
        "person and a burglar, between a cat on the porch and a person trying to "
        "break in. SentinelNet does the same thing, but instead of watching video, "
        "it watches streams of network data. And instead of recognizing faces, it "
        "recognizes attack patterns hidden inside the numbers.")

    # ═══════════════════ CHAPTER 2 ═══════════════════
    add_chapter(pdf, 2, "How Does It Work?")

    add_section(pdf, "The Big Picture")
    add_para(pdf,
        "SentinelNet AI works as a pipeline -- data flows through a series of steps, "
        "each step transforming it a little more until the AI can make a decision. "
        "Here is the full pipeline, step by step:")

    add_subsection(pdf, "Step 1: Packet Capture")
    add_para(pdf,
        "Everything on a network travels in small chunks called 'packets'. Think of "
        "them as envelopes: each one has a sender address, a recipient address, and "
        "some data inside. SentinelNet uses a tool called Scapy to intercept these "
        "packets as they flow through your computer's network interface. It is like "
        "sitting at the mailroom and reading every envelope that comes through.")
    add_note(pdf,
        "On most systems, capturing raw packets requires administrator (root) "
        "privileges. SentinelNet has a fallback mode that works without root, "
        "making it perfect for demos on your laptop.")

    add_subsection(pdf, "Step 2: Flow Aggregation")
    add_para(pdf,
        "Individual packets are not very useful on their own. Imagine trying to "
        "understand a phone conversation by hearing one word at a time, out of order. "
        "Instead, SentinelNet groups packets into 'flows' -- complete conversations "
        "between two computers. A flow is identified by 5 things: source IP, "
        "destination IP, source port, destination port, and protocol (TCP/UDP). "
        "All packets sharing these 5 values belong to the same flow.")
    add_para(pdf,
        "The Flow Manager keeps track of active flows and closes them after a period "
        "of inactivity (idle timeout) or after a maximum duration (active timeout). "
        "This ensures the system does not wait forever for a flow to end.")

    add_subsection(pdf, "Step 3: Feature Extraction")
    add_para(pdf,
        "Once a flow is complete, SentinelNet calculates 22 statistical features "
        "from it. These numbers summarize the entire conversation in a way the AI "
        "can understand. Some examples:")
    add_bullet(pdf, "Duration: How long did the conversation last?")
    add_bullet(pdf, "Packet count: How many packets were sent forward and backward?")
    add_bullet(pdf, "Byte count: How much data was transferred?")
    add_bullet(pdf, "Packet size stats: Average, minimum, maximum, and standard deviation")
    add_bullet(pdf, "Timing stats: Average and variation of time between packets")
    add_bullet(pdf, "Flow rate: Packets per second and bytes per second")
    add_bullet(pdf, "TCP flags: Counts of SYN, ACK, FIN, RST, PSH, URG flags")
    add_para(pdf,
        "These 22 numbers are like a fingerprint of the conversation. Normal browsing "
        "has a very different fingerprint than a port scan or a DDoS flood.")

    add_subsection(pdf, "Step 4: AI Classification (The Deep Learning Part)")
    add_para(pdf,
        "The 22 features are fed into a 1D Convolutional Neural Network (1D-CNN). "
        "This is the brain of SentinelNet. Here is what happens inside:")
    add_numbered(pdf, 1, "The 22 features are treated as a 1-dimensional signal (like audio).")
    add_numbered(pdf, 2, "Three convolutional layers scan for patterns in the feature vector, "
                 "each layer finding increasingly complex patterns.")
    add_numbered(pdf, 3, "Batch normalization and dropout prevent overfitting (memorizing "
                 "instead of learning).")
    add_numbered(pdf, 4, "Dense (fully connected) layers combine the patterns into a final "
                 "classification.")
    add_numbered(pdf, 5, "A softmax layer outputs 5 probabilities, one for each attack category.")
    add_para(pdf,
        "The category with the highest probability becomes the prediction. The model "
        "also outputs a confidence score (0% to 100%) telling you how sure it is.")

    add_para(pdf, "Model specifications:")
    add_simple_table(pdf,
        ["Property", "Value"],
        [
            ["Architecture", "1D-CNN (3 conv layers + 3 dense)"],
            ["Input", "22 flow features"],
            ["Output", "5 classes with probabilities"],
            ["Training samples", "20,000 flows"],
            ["Test accuracy", "99.97%"],
            ["Inference time", "< 5 ms per flow"],
            ["Framework", "PyTorch (CPU)"],
        ],
        [70, 120])

    add_subsection(pdf, "Step 5: Risk Assessment")
    add_para(pdf,
        "After the AI classifies a flow, the Risk Engine assigns a human-readable "
        "risk level. This makes it easy for anyone to understand the severity:")
    add_simple_table(pdf,
        ["Risk Level", "Color", "When It Happens"],
        [
            ["NORMAL", "Green", "BENIGN with high confidence (>= 70%)"],
            ["LOW", "Blue", "BENIGN with low confidence, or minor anomaly"],
            ["MEDIUM", "Yellow", "Attack detected with moderate confidence (30-60%)"],
            ["HIGH", "Orange", "Attack detected with high confidence (60-85%)"],
            ["CRITICAL", "Red", "Attack with very high confidence (>= 85%)"],
        ],
        [35, 25, 130])

    add_subsection(pdf, "Step 6: Real-Time Dashboard")
    add_para(pdf,
        "Everything is displayed on a live web dashboard using WebSocket technology. "
        "WebSockets allow the server to push updates to your browser the instant a "
        "new detection happens -- no need to refresh the page. The dashboard shows "
        "charts, tables, alerts, and statistics, all updating in real time.")

    # ═══════════════════ CHAPTER 3 ═══════════════════
    add_chapter(pdf, 3, "What You Need (Prerequisites)")

    add_section(pdf, "Hardware Requirements")
    add_simple_table(pdf,
        ["Component", "Minimum", "Recommended"],
        [
            ["CPU", "Any modern x86_64", "Intel i5 / AMD Ryzen 5 or better"],
            ["RAM", "2 GB free", "4 GB free"],
            ["Disk Space", "500 MB", "1 GB"],
            ["GPU", "Not required", "Not required"],
            ["Network", "Loopback (localhost)", "Any network interface"],
        ],
        [45, 65, 80])

    add_section(pdf, "Software Requirements")
    add_bullet(pdf, "Operating System: Linux (Fedora, Ubuntu, Debian, CentOS, etc.)")
    add_bullet(pdf, "Python: Version 3.10 or higher (3.12 recommended)")
    add_bullet(pdf, "pip: Python package manager (comes with Python)")
    add_bullet(pdf, "Web Browser: Chrome, Firefox, Edge, or Safari")
    add_bullet(pdf, "Terminal: Any terminal emulator (GNOME Terminal, Konsole, etc.)")
    add_para(pdf, "")
    add_note(pdf,
        "You do NOT need a GPU. SentinelNet AI runs entirely on CPU, making it "
        "accessible on any laptop or desktop. The model is small enough (~140K "
        "parameters) that CPU inference takes less than 5 milliseconds.")

    add_section(pdf, "Knowledge Requirements")
    add_para(pdf,
        "You only need basic skills to run SentinelNet AI:")
    add_bullet(pdf, "How to open a terminal and type commands")
    add_bullet(pdf, "How to open a web browser")
    add_bullet(pdf, "Basic understanding of files and folders")
    add_para(pdf,
        "That is it! You do NOT need to know Python programming, machine learning, "
        "or networking to run the demo. This guide will walk you through every step.")

    # ═══════════════════ CHAPTER 4 ═══════════════════
    add_chapter(pdf, 4, "Installation Step-by-Step")

    add_section(pdf, "Step 1: Get the Project Files")
    add_para(pdf,
        "First, make sure you have the SentinelNet AI project folder on your "
        "computer. If you received it as a zip file, extract it. If it is on "
        "a USB drive, copy it to your home directory. The folder should be "
        "named 'sentinel' and contain subfolders like backend/, ml/, frontend/, etc.")
    add_code(pdf,
        "# Example: If you have a zip file\n"
        "unzip sentinelnet-ai.zip\n"
        "# or clone from git\n"
        "# git clone <repository-url> sentinel")
    add_para(pdf,
        "Navigate to the project folder in your terminal:")
    add_code(pdf, "cd ~/sentinel")

    add_section(pdf, "Step 2: Create a Python Virtual Environment")
    add_para(pdf,
        "A virtual environment is like a separate, clean room for your project's "
        "Python packages. It prevents conflicts with other Python projects on your "
        "system. Run these commands:")
    add_code(pdf,
        "# Create the virtual environment\n"
        "python3 -m venv venv\n\n"
        "# Activate it (you will see '(venv)' appear in your prompt)\n"
        "source venv/bin/activate")
    add_tip(pdf,
        "You need to activate the virtual environment every time you open a new "
        "terminal. Just run: source venv/bin/activate")

    add_section(pdf, "Step 3: Install Dependencies")
    add_para(pdf,
        "Now install all the Python packages that SentinelNet needs:")
    add_code(pdf, "pip install -r requirements.txt")
    add_para(pdf,
        "This will download and install about 15 packages including PyTorch, "
        "FastAPI, Scapy, and more. It may take 2-5 minutes depending on your "
        "internet speed.")
    add_note(pdf,
        "If you see SSL certificate errors, try adding these flags:\n"
        "pip install -r requirements.txt --trusted-host pypi.org "
        "--trusted-host files.pythonhosted.org")

    add_section(pdf, "Step 4: Train the AI Model")
    add_para(pdf,
        "If the models/ folder already contains sentinelnet_model.pt, you can skip "
        "this step. Otherwise, train the model:")
    add_code(pdf, "PYTHONPATH=. python ml/train.py")
    add_para(pdf,
        "This will: (a) generate 20,000 training samples, (b) train the neural "
        "network for up to 50 epochs, and (c) save the trained model to the models/ "
        "folder. Training takes about 1-3 minutes on a modern CPU.")
    add_note(pdf,
        "The PYTHONPATH=. at the start is important! It tells Python where to find "
        "the project modules. Always include it when running commands from the "
        "sentinel folder.")

    add_section(pdf, "Step 5: Start the Server")
    add_para(pdf, "Launch the SentinelNet AI server:")
    add_code(pdf,
        "PYTHONPATH=. python -m uvicorn backend.main:app \\\n"
        "    --host 127.0.0.1 --port 8000")
    add_para(pdf,
        "You should see output like:\n"
        "  INFO:     Started server process [12345]\n"
        "  INFO:     Uvicorn running on http://127.0.0.1:8000\n\n"
        "The server is now running! Leave this terminal open.")

    add_section(pdf, "Step 6: Open the Dashboard")
    add_para(pdf,
        "Open your web browser and go to:")
    add_code(pdf, "http://127.0.0.1:8000")
    add_para(pdf,
        "You should see the SentinelNet AI SOC Dashboard -- a dark-themed "
        "cybersecurity control panel. Congratulations, the system is running!")

    add_section(pdf, "Quick Start Summary")
    add_simple_table(pdf,
        ["Step", "Command", "What It Does"],
        [
            ["1", "cd ~/sentinel", "Go to project folder"],
            ["2", "source venv/bin/activate", "Activate Python env"],
            ["3", "pip install -r requirements.txt", "Install packages"],
            ["4", "PYTHONPATH=. python ml/train.py", "Train the AI model"],
            ["5", "PYTHONPATH=. python -m uvicorn ...", "Start the server"],
            ["6", "Open browser to localhost:8000", "View dashboard"],
        ],
        [15, 80, 95])

    # ═══════════════════ CHAPTER 5 ═══════════════════
    add_chapter(pdf, 5, "Using the Dashboard")

    add_section(pdf, "Dashboard Overview")
    add_para(pdf,
        "The SentinelNet AI dashboard is designed to look like a professional "
        "Security Operations Center (SOC). It uses a dark theme with cyber-style "
        "colors -- this is not just for looks, dark themes reduce eye strain during "
        "long monitoring sessions, which is standard practice in real SOCs.")

    add_section(pdf, "Dashboard Components")

    add_subsection(pdf, "1. Status Bar (Top)")
    add_para(pdf,
        "At the top of the dashboard you will find status indicators showing:\n"
        "  - System Status: Whether the monitoring engine is running (green) or stopped (red)\n"
        "  - Model Status: Whether the AI model is loaded and ready\n"
        "  - WebSocket: Whether the real-time connection to the server is active")

    add_subsection(pdf, "2. Statistics Panel")
    add_para(pdf,
        "A row of cards showing key numbers:\n"
        "  - Total Flows Analyzed: How many network conversations have been processed\n"
        "  - Threats Detected: How many malicious flows were found\n"
        "  - Detection Rate: Percentage of flows that were threats\n"
        "  - Active Alerts: Number of currently active high-severity alerts")

    add_subsection(pdf, "3. Traffic Distribution Chart (Pie Chart)")
    add_para(pdf,
        "A colorful pie chart showing the breakdown of traffic by category. In a "
        "healthy network, this should be mostly 'BENIGN' (green). If you see large "
        "slices of red (DoS/DDoS) or orange (PortScan), something is wrong.")

    add_subsection(pdf, "4. Timeline Chart (Line Chart)")
    add_para(pdf,
        "A line chart showing detections over time. This helps you spot attack "
        "patterns -- for example, you might see a spike in PortScan activity "
        "followed by a DoS attack, which is a common attack pattern.")

    add_subsection(pdf, "5. Live Detection Table")
    add_para(pdf,
        "The main table showing every analyzed flow. Each row includes:\n"
        "  - Timestamp: When the flow was detected\n"
        "  - Source IP and Port: Where the traffic came from\n"
        "  - Destination IP and Port: Where it was going\n"
        "  - Protocol: TCP or UDP\n"
        "  - Classification: What the AI thinks it is (BENIGN, DoS_DDoS, etc.)\n"
        "  - Confidence: How sure the AI is (0-100%)\n"
        "  - Risk Level: Color-coded severity (NORMAL to CRITICAL)\n\n"
        "New rows appear at the top as detections happen in real time.")

    add_subsection(pdf, "6. Alert Banner")
    add_para(pdf,
        "When a CRITICAL or HIGH risk threat is detected, a red alert banner "
        "flashes at the top of the screen. This ensures you never miss a serious "
        "threat, even if you are not actively watching the detection table.")

    add_subsection(pdf, "7. Demo Control Buttons")
    add_para(pdf,
        "At the bottom of the dashboard, you will find buttons to trigger demo "
        "traffic. These let you generate safe, fake attack traffic to see how "
        "the system responds. More on this in Chapter 6.")

    # ═══════════════════ CHAPTER 6 ═══════════════════
    add_chapter(pdf, 6, "Running the Live Demo")

    add_section(pdf, "Why a Live Demo Matters")
    add_para(pdf,
        "This is the most important part of the project! The live demo proves that "
        "SentinelNet AI is not just a static machine learning model that runs on a "
        "CSV file. It is a complete, working system that captures traffic, analyzes "
        "it with AI, and displays results in real time.")

    add_section(pdf, "How to Run the Demo")
    add_para(pdf,
        "There are two ways to trigger demo traffic:")

    add_subsection(pdf, "Method 1: Use the Dashboard Buttons")
    add_para(pdf,
        "Simply click the demo buttons on the dashboard. Each button generates a "
        "different type of traffic.")

    add_subsection(pdf, "Method 2: Use curl Commands in the Terminal")
    add_para(pdf,
        "Open a NEW terminal (keep the server running in the first one). Then run "
        "these commands one at a time:")
    add_para(pdf, "")

    add_bold_para(pdf, "Generate Normal (Safe) Traffic:")
    add_code(pdf, "curl http://127.0.0.1:8000/api/demo/trigger?mode=normal")
    add_para(pdf,
        "This simulates regular web browsing and file downloads. On the dashboard, "
        "you should see new rows appearing with classification 'BENIGN' and risk "
        "level 'NORMAL' (green).")

    add_bold_para(pdf, "Generate a Port Scan Attack:")
    add_code(pdf, "curl http://127.0.0.1:8000/api/demo/trigger?mode=portscan")
    add_para(pdf,
        "This simulates an attacker scanning your computer for open ports. On the "
        "dashboard, you will see detections classified as 'PortScan' with risk level "
        "'HIGH' or 'CRITICAL' (orange/red). The alert banner should flash!")

    add_bold_para(pdf, "Generate a SYN Flood (DDoS) Attack:")
    add_code(pdf, "curl http://127.0.0.1:8000/api/demo/trigger?mode=synflood")
    add_para(pdf,
        "This simulates a Denial of Service attack where the attacker floods your "
        "system with connection requests. The dashboard will show 'DoS_DDoS' "
        "classifications with 'CRITICAL' risk level and 100% confidence.")

    add_bold_para(pdf, "Generate a UDP Flood Attack:")
    add_code(pdf, "curl http://127.0.0.1:8000/api/demo/trigger?mode=udpflood")
    add_para(pdf,
        "Similar to SYN flood but using UDP protocol. Again classified as 'DoS_DDoS' "
        "with 'CRITICAL' risk level.")

    add_section(pdf, "What to Watch For During the Demo")
    add_numbered(pdf, 1, "New rows appearing instantly in the detection table")
    add_numbered(pdf, 2, "The pie chart updating to show the new traffic distribution")
    add_numbered(pdf, 3, "The timeline chart showing spikes when attacks happen")
    add_numbered(pdf, 4, "The alert banner flashing red for high-severity threats")
    add_numbered(pdf, 5, "Statistics counters incrementing in real time")
    add_numbered(pdf, 6, "Different colors for different risk levels in the table")

    add_section(pdf, "Recommended Demo Sequence")
    add_para(pdf,
        "For the best demonstration during a presentation, follow this sequence:")
    add_numbered(pdf, 1, "Start the server and open the dashboard")
    add_numbered(pdf, 2, "Generate some normal traffic first to establish a baseline")
    add_numbered(pdf, 3, "Wait a few seconds, then trigger a port scan")
    add_numbered(pdf, 4, "Point out how the AI immediately detects the attack")
    add_numbered(pdf, 5, "Trigger a SYN flood and show the CRITICAL alert")
    add_numbered(pdf, 6, "Show the pie chart shifting from mostly green to mixed colors")
    add_numbered(pdf, 7, "Show the timeline chart with the visible attack spike")

    add_warning(pdf,
        "The demo traffic is completely safe! It only generates traffic on "
        "localhost (127.0.0.1) and never touches your real network. You can run "
        "it as many times as you want without any risk.")

    # ═══════════════════ CHAPTER 7 ═══════════════════
    add_chapter(pdf, 7, "Understanding the Results")

    add_section(pdf, "Attack Categories Explained in Detail")

    add_subsection(pdf, "BENIGN (Normal Traffic)")
    add_para(pdf,
        "This is safe, everyday network traffic. Web browsing, email, file "
        "downloads, streaming video -- all of these produce BENIGN traffic. "
        "In a healthy network, the vast majority of traffic should be BENIGN.")

    add_subsection(pdf, "Bot / Infiltration")
    add_para(pdf,
        "A 'bot' is a computer that has been secretly taken over by malware and "
        "is being controlled remotely. Botnets (networks of bots) are used for "
        "sending spam, mining cryptocurrency, or launching coordinated attacks. "
        "Infiltration means someone has successfully broken into the network and "
        "is moving around inside it, stealing data or planting backdoors.")

    add_subsection(pdf, "Brute Force")
    add_para(pdf,
        "A brute force attack is when an attacker tries to guess a password by "
        "trying every possible combination. For example, they might try 'password1', "
        "'password2', 'password3', and so on, thousands of times per second. This "
        "creates a distinctive pattern in the network traffic that SentinelNet "
        "can recognize: many short connections to the same target, each with "
        "similar sizes.")

    add_subsection(pdf, "DoS / DDoS (Denial of Service)")
    add_para(pdf,
        "DoS (Denial of Service) attacks try to make a service unavailable by "
        "overwhelming it with traffic. DDoS (Distributed Denial of Service) is "
        "the same thing but from many different sources at once. In a SYN flood, "
        "the attacker sends millions of connection requests (SYN packets) without "
        "ever completing them, which exhausts the target's resources.")
    add_para(pdf,
        "SentinelNet detects these by noticing extremely high packet rates, "
        "asymmetric flow patterns (many packets sent, few received), and "
        "unusual flag distributions (all SYN, no ACK).")

    add_subsection(pdf, "Port Scan")
    add_para(pdf,
        "Port scanning is the network equivalent of a burglar checking every "
        "door and window of a house to find one that is unlocked. The attacker "
        "sends packets to many different ports on your computer to see which "
        "services are running. This is usually the first step before a real "
        "attack. SentinelNet detects this by noticing many short connections "
        "to different ports from the same source.")

    add_section(pdf, "Risk Levels Explained")
    add_simple_table(pdf,
        ["Level", "Color", "Meaning", "Action Needed"],
        [
            ["NORMAL", "Green", "Safe, no threats", "None"],
            ["LOW", "Blue", "Minor anomaly", "Monitor"],
            ["MEDIUM", "Yellow", "Suspicious activity", "Investigate"],
            ["HIGH", "Orange", "Likely an attack", "Respond quickly"],
            ["CRITICAL", "Red", "Active attack", "Immediate action!"],
        ],
        [30, 25, 60, 75])

    add_section(pdf, "Understanding Confidence Scores")
    add_para(pdf,
        "Every detection comes with a confidence score from 0% to 100%. This "
        "tells you how sure the AI is about its classification:")
    add_bullet(pdf, "90-100%: Very confident -- the AI is almost certain")
    add_bullet(pdf, "70-89%: Confident -- likely correct")
    add_bullet(pdf, "50-69%: Moderate -- could go either way")
    add_bullet(pdf, "Below 50%: Low confidence -- take with a grain of salt")
    add_para(pdf,
        "In practice, SentinelNet's confidence scores are usually very high "
        "(95-100%) because the model is well-trained. If you see a low-confidence "
        "detection, it usually means the traffic has characteristics of both "
        "normal and attack patterns.")

    # ═══════════════════ CHAPTER 8 ═══════════════════
    add_chapter(pdf, 8, "Project File Structure")

    add_section(pdf, "Directory Layout")
    add_para(pdf,
        "Here is what each folder and key file does:")

    add_simple_table(pdf,
        ["Folder / File", "Purpose"],
        [
            ["backend/", "FastAPI server, REST API, WebSocket manager"],
            ["backend/main.py", "Main entry point -- starts the server"],
            ["backend/api/routes.py", "All API endpoints (URLs you can call)"],
            ["backend/services/", "Core business logic"],
            ["capture/", "Packet capture and flow management"],
            ["capture/packet_capture.py", "Intercepts network packets"],
            ["capture/flow_manager.py", "Groups packets into flows"],
            ["capture/feature_extractor.py", "Calculates the 22 features"],
            ["ml/", "Machine learning / deep learning code"],
            ["ml/model.py", "Neural network architecture"],
            ["ml/train.py", "Training pipeline"],
            ["ml/predictor.py", "Makes predictions on new flows"],
            ["database/", "Database models and connection"],
            ["frontend/", "Web dashboard (HTML, CSS, JavaScript)"],
            ["demo/", "Safe demo traffic generator"],
            ["models/", "Trained model files (.pt, .joblib)"],
            ["tests/", "Automated test suite (19 tests)"],
            ["data/", "Training dataset CSV"],
            ["docs/", "Documentation and PDFs"],
        ],
        [75, 115])

    add_section(pdf, "Key Model Files")
    add_simple_table(pdf,
        ["File", "What It Contains"],
        [
            ["models/sentinelnet_model.pt", "Trained PyTorch neural network weights"],
            ["models/scaler.joblib", "StandardScaler for feature normalization"],
            ["models/label_encoder.joblib", "Maps class numbers to names"],
            ["models/feature_names.json", "List of 22 feature column names"],
            ["models/model_metrics.json", "Evaluation results (accuracy, etc.)"],
            ["models/confusion_matrix.png", "Visual confusion matrix plot"],
        ],
        [80, 110])

    # ═══════════════════ CHAPTER 9 ═══════════════════
    add_chapter(pdf, 9, "Troubleshooting Common Issues")

    add_section(pdf, "Problem: 'Permission denied' when capturing packets")
    add_para(pdf,
        "Cause: Raw packet capture requires root/administrator privileges.\n"
        "Solution: SentinelNet automatically falls back to user-space capture mode. "
        "The demo traffic generator bypasses raw sockets entirely, so the demo "
        "always works regardless of permissions. You do not need to fix this for "
        "the demonstration.")

    add_section(pdf, "Problem: Port 8000 already in use")
    add_para(pdf, "Cause: Another program is using port 8000.")
    add_code(pdf,
        "# Find and kill the process using port 8000\n"
        "lsof -i :8000\n"
        "kill <PID>\n\n"
        "# Or start on a different port\n"
        "PYTHONPATH=. python -m uvicorn backend.main:app --port 8080")

    add_section(pdf, "Problem: 'Model not found' error")
    add_para(pdf,
        "Cause: The model has not been trained yet.\n"
        "Solution: Run the training command:")
    add_code(pdf, "PYTHONPATH=. python ml/train.py")

    add_section(pdf, "Problem: Dashboard is blank or not loading")
    add_para(pdf,
        "Check these things in order:\n"
        "  1. Is the server running? Check the terminal for errors.\n"
        "  2. Are you using the right URL? http://127.0.0.1:8000\n"
        "  3. Try a hard refresh: Ctrl+Shift+R\n"
        "  4. Check browser console (F12) for JavaScript errors.")

    add_section(pdf, "Problem: Database errors")
    add_para(pdf,
        "SentinelNet supports two databases: MariaDB (primary) and SQLite (fallback). "
        "If MariaDB is not installed or configured, the system automatically uses "
        "SQLite. You should see a message like:\n"
        "  'MariaDB not available, falling back to SQLite'\n\n"
        "This is perfectly normal for development and demos.")

    add_section(pdf, "Problem: pip install fails with SSL errors")
    add_para(pdf, "Try adding trust flags:")
    add_code(pdf,
        "pip install -r requirements.txt \\\n"
        "    --trusted-host pypi.org \\\n"
        "    --trusted-host files.pythonhosted.org")

    add_section(pdf, "Problem: ModuleNotFoundError")
    add_para(pdf,
        "Cause: You forgot to set PYTHONPATH or activate the virtual environment.\n"
        "Solution: Always run commands like this:")
    add_code(pdf,
        "# Make sure venv is activated\n"
        "source venv/bin/activate\n\n"
        "# Always set PYTHONPATH\n"
        "PYTHONPATH=. python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000")

    # ═══════════════════ CHAPTER 10 ═══════════════════
    add_chapter(pdf, 10, "Frequently Asked Questions")

    questions = [
        ("Is this safe to run on my laptop?",
         "Yes! The demo traffic generator only creates traffic on localhost "
         "(127.0.0.1). It never sends any data to the internet or other computers "
         "on your network. It is completely safe to run during a presentation."),

        ("Can I use this on a real network?",
         "With modifications, yes. You would need: (a) root/admin privileges for "
         "raw packet capture, (b) proper network interface configuration, (c) "
         "retraining on real-world data for better accuracy, and (d) proper security "
         "considerations for a production deployment."),

        ("What dataset was it trained on?",
         "SentinelNet was trained on 20,000 flow records generated following the "
         "statistical distribution of the CICIDS2017 dataset, which is one of the "
         "most widely used benchmark datasets for intrusion detection research. "
         "It was created by the Canadian Institute for Cybersecurity."),

        ("Can I add more attack types?",
         "Yes! You would need to: (a) add new attack categories to the training "
         "data, (b) update the model's output layer to support more classes, and "
         "(c) retrain the model. The training pipeline is designed to be easily "
         "extendable."),

        ("Why is the accuracy so high (99.97%)?",
         "The high accuracy is because the benchmark data has clear statistical "
         "differences between attack categories. Real-world traffic can be more "
         "nuanced, so accuracy in production would likely be somewhat lower. "
         "However, the architecture and approach are sound."),

        ("Do I need a GPU?",
         "No! The model is small enough (~140,000 parameters) that CPU inference "
         "takes less than 5 milliseconds per flow. A GPU would help only if you "
         "needed to retrain the model on millions of samples."),

        ("How do I stop the server?",
         "Press Ctrl+C in the terminal where the server is running."),

        ("Can I change the dashboard theme?",
         "Yes, the dashboard is built with HTML, CSS, and JavaScript. You can "
         "modify the files in the frontend/ folder. The CSS is in "
         "frontend/css/style.css."),

        ("What happens if the AI makes a wrong prediction?",
         "Like all AI systems, SentinelNet can make mistakes. In the test set, "
         "there was only 1 misclassification out of 3,000 samples: one normal "
         "flow was classified as BruteForce. In production, you would want human "
         "analysts to review high-severity alerts."),

        ("Can I run this on Windows or Mac?",
         "The project was developed on Linux, but with minor modifications "
         "(mainly the packet capture module), it could work on Windows or macOS. "
         "The easiest approach on Windows would be to use WSL (Windows Subsystem "
         "for Linux)."),
    ]

    for q, a in questions:
        add_subsection(pdf, f"Q: {q}")
        add_para(pdf, a)

    # ────────────────────── FINAL PAGE ──────────────────────
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 70, 140)
    pdf.cell(0, 14, "You're Ready!", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 14)
    pdf.multi_cell(0, 8, safe(
        "You now have everything you need to install, run, and demonstrate "
        "SentinelNet AI. Remember the key steps:\n\n"
        "1. Activate the virtual environment\n"
        "2. Start the server with PYTHONPATH=.\n"
        "3. Open the dashboard in your browser\n"
        "4. Use the demo buttons to generate traffic\n"
        "5. Watch the AI detect attacks in real time!\n\n"
        "Good luck with your project presentation!"
    ), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # ────────────────────── SAVE ──────────────────────
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    pdf.output(OUTPUT_PATH)
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"Beginner Guide PDF generated: {OUTPUT_PATH}")
    print(f"Size: {size_kb:.1f} KB")
    print(f"Pages: {pdf.page_no()}")


if __name__ == "__main__":
    generate()

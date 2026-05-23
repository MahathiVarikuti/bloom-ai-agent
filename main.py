#!/usr/bin/env python3
# main.py - CLI runner for the Bloom Aesthetics AI Agent
#
# Usage:
#   python main.py
#
# Commands during chat:
#   'quit' / 'bye' / 'exit' - end session and generate summary
#   'summary'               - same as above
#   Ctrl+C                  - graceful exit

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from agent import BloomAgent, Stage
from config import COLORS as C


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def bold(text):    return f"{C['bold']}{text}{C['reset']}"
def dim(text):     return f"{C['dim']}{text}{C['reset']}"
def cyan(text):    return f"{C['cyan']}{text}{C['reset']}"
def green(text):   return f"{C['green']}{text}{C['reset']}"
def yellow(text):  return f"{C['yellow']}{text}{C['reset']}"
def red(text):     return f"{C['red']}{text}{C['reset']}"
def magenta(text): return f"{C['magenta']}{text}{C['reset']}"


def print_banner():
    print(f"""
{C['cyan']}{C['bold']}
  ╔══════════════════════════════════════════╗
  ║         Bloom Aesthetics Clinic          ║
  ║         AI Support Agent - Aria          ║
  ╚══════════════════════════════════════════╝
{C['reset']}""")


def print_aria(text, confidence=None, stage=None):
    prefix = cyan(bold("Aria:"))
    meta_parts = []
    if confidence and confidence != "high":
        meta_parts.append(f"confidence: {confidence}")
    if stage and stage != Stage.FAQ:
        meta_parts.append(f"stage: {stage.value}")
    meta = f"  {dim('[' + ', '.join(meta_parts) + ']')}" if meta_parts else ""
    print(f"\n{prefix} {text}{meta}")


def print_system(text):
    print(f"\n{dim(text)}")


def print_escalation(reason):
    print(f"\n{red(bold('🚨 ESCALATION TRIGGERED'))}")
    print(f"   {red('Reason:')} {reason}")
    print(f"   {dim('Flagged for human handoff.')}")


def print_sop_gap(gap):
    print(f"\n{yellow('SOP gap logged:')} {dim(gap)}")


def print_summary(summary: dict):
    print(f"\n{magenta(bold('=' * 52))}")
    print(magenta(bold("             SESSION SUMMARY")))
    print(magenta(bold('=' * 52)))

    if not isinstance(summary, dict):
        print(f"\n{red('Could not generate summary.')}")
        return

    print(f"\n{bold('Customer Intent')}")
    print(f"  {summary.get('customer_intent', 'N/A')}")

    kd = summary.get("key_details", {})
    if kd:
        print(f"\n{bold('Key Details')}")
        for k, v in kd.items():
            if v:
                label = k.replace("_", " ").title()
                print(f"  {label}: {v}")

    qs = summary.get("qualification_summary", {})
    if any(qs.values()):
        print(f"\n{bold('Qualification Data')}")
        for k, v in qs.items():
            if v and v not in ("unknown", "not provided", ""):
                label = k.replace("_", " ").title()
                print(f"  {label}: {v}")

    gaps = summary.get("sop_gaps_identified", [])
    if gaps:
        print(f"\n{yellow(bold('SOP Gaps Identified'))}")
        for gap in gaps:
            print(f"  • {gap}")

    esc = summary.get("escalation", {})
    if esc.get("was_escalated"):
        print(f"\n{red(bold('Escalation'))}")
        print(f"  Reason: {esc.get('reason', 'N/A')}")
        if esc.get("trigger_message"):
            print(f"  Triggered by: \"{esc['trigger_message']}\"")

    print(f"\n{green(bold('Recommended Next Action'))}")
    print(f"  {summary.get('recommended_next_action', 'N/A')}")

    print(f"\n{magenta(bold('=' * 52))}\n")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run():
    print_banner()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print(red("Error: OPENROUTER_API_KEY is not set."))
        print(dim("Copy .env.example to .env and add your API key, then try again."))
        sys.exit(1)

    print(dim("Type your message to chat with Aria."))
    print(dim("Type 'quit', 'bye', or 'summary' to end the session and see the summary.\n"))

    agent = BloomAgent()

    # Kick off with a warm greeting so the customer isn't staring at a blank screen
    greeting = agent.chat("Hello, I've just arrived on the website.")
    print_aria(greeting.message)

    while True:
        try:
            user_input = input(f"\n{green('You:')} ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            user_input = "quit"

        if not user_input:
            continue

        # Exit commands
        if user_input.lower() in ("quit", "bye", "exit", "summary", "q"):
            print_system("Wrapping up — generating session summary...")

            summary = agent.generate_summary()
            print_summary(summary)

            # Save session log
            os.makedirs("logs", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = f"logs/session_{ts}.json"
            agent.save_session(log_path)
            print_system(f"Session log saved → {log_path}")
            break

        response = agent.chat(user_input)

        # Surface escalation prominently
        if response.escalated:
            print_escalation(response.escalation_reason)

        print_aria(response.message, confidence=response.confidence, stage=response.stage)

        # Surface SOP gaps in dim text so they're visible but not alarming to the customer
        # (in a real deployment this would only go to internal logs)
        if response.sop_gap:
            print_sop_gap(response.sop_gap)


if __name__ == "__main__":
    run()

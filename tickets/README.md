# Tickets Directory

This directory contains all the ticket files for the project.

## Important Guidelines

**⚠️ Always use ticket.sh commands to manage tickets:**

- **Create new tickets:** `bash ./scripts/ticket.sh new <slug>`
- **Start working on a ticket:** `bash ./scripts/ticket.sh start <ticket-name>`
- **Complete a ticket:** `bash ./scripts/ticket.sh close`

**❌ DO NOT manually merge feature branches to the default branch!**
The `bash ./scripts/ticket.sh close` command handles merging and cleanup automatically.

## Directory Structure

- Active tickets: `*.md` files in this directory
- Completed tickets: `done/` subdirectory (created automatically)

## Getting Help

For detailed usage instructions, run:
# Ticket Management System for Coding Agents
Version: 20250718.041428
https://github.com/masuidrive/ticket.sh

## Overview

This is a self-contained ticket management system using shell script + files + Git.
Each ticket is a single Markdown file with YAML frontmatter metadata.

## Usage

- `bash ./scripts/ticket.sh init` - Initialize system (create config, directories, .gitignore)
- `bash ./scripts/ticket.sh new <slug>` - Create new ticket file (slug: lowercase, numbers, hyphens only)
- `bash ./scripts/ticket.sh list [--status STATUS] [--count N]` - List tickets (default: todo + doing, count: 20)
- `bash ./scripts/ticket.sh start <ticket-name>` - Start working on ticket (creates or switches to feature branch)
- `bash ./scripts/ticket.sh restore` - Restore current-ticket.md symlink from branch name
- `bash ./scripts/ticket.sh check` - Check current directory and ticket/branch synchronization status
- `bash ./scripts/ticket.sh close [--no-push] [--force|-f] [--no-delete-remote]` - Complete current ticket (squash merge to default branch)
- `bash ./scripts/ticket.sh selfupdate` - Update ticket.sh to the latest version from GitHub
- `bash ./scripts/ticket.sh version` - Display version information
- `bash ./scripts/ticket.sh prompt` - Display prompt instructions for AI coding assistants

## Ticket Naming

- Format: `YYMMDD-hhmmss-<slug>`
- Example: `241225-143502-implement-user-auth`
- Generated automatically when creating tickets

## Ticket Status

- `todo`: not started (started_at: null)
- `doing`: in progress (started_at set, closed_at: null)
- `done`: completed (closed_at set)

## Configuration

- Config file: `.ticket-config.yaml` or `.ticket-config.yml` (in project root)
- Initialize with: `bash ./scripts/ticket.sh init`
- Edit to customize directories, branches, templates, and success messages

### Success Messages

- `new_success_message`: Displayed after creating a new ticket
- `start_success_message`: Displayed after starting work on a ticket
- `restore_success_message`: Displayed after restoring current ticket link
- `close_success_message`: Displayed after closing a ticket
- All messages default to empty (disabled) and support multiline YAML format

## Push Control

- Set `auto_push: false` in config to disable automatic pushing for close command
- Use `--no-push` flag with close command to skip pushing
- Feature branches are always created locally (no auto-push on start)
- Git commands and outputs are displayed for transparency

## Workflow

### Create New Ticket

1. Create ticket: `bash ./scripts/ticket.sh new feature-name`
2. Edit ticket content and description in the generated file

### Start Work

1. Check available tickets: `bash ./scripts/ticket.sh list` or browse tickets directory
2. Start work: `bash ./scripts/ticket.sh start 241225-143502-feature-name`
3. Develop on feature branch (`current-ticket.md` shows active ticket)

### Closing

1. Before closing:
   - Review ticket content and description
   - Check all tasks in checklist are completed (mark with `[x]`)
   - Get user approve before proceeding
2. Complete: `bash ./scripts/ticket.sh close`

**Note**: If specific workflow instructions are provided elsewhere (e.g., in project documentation or CLAUDE.md), those take precedence over this general workflow.

## Troubleshooting

- Run from project root (where `.git` and config file exist)
- Use `restore` if `current-ticket.md` is missing after clone/pull
- Check `list` to see available tickets and their status
- Ensure Git working directory is clean before start/close

**Note**: `current-ticket.md` is git-ignored and needs `restore` after clone/pull.

For a list of all available commands:
# Ticket Management System for Coding Agents
Version: 20250718.041428
https://github.com/masuidrive/ticket.sh

## Overview

This is a self-contained ticket management system using shell script + files + Git.
Each ticket is a single Markdown file with YAML frontmatter metadata.

## Usage

- `bash ./scripts/ticket.sh init` - Initialize system (create config, directories, .gitignore)
- `bash ./scripts/ticket.sh new <slug>` - Create new ticket file (slug: lowercase, numbers, hyphens only)
- `bash ./scripts/ticket.sh list [--status STATUS] [--count N]` - List tickets (default: todo + doing, count: 20)
- `bash ./scripts/ticket.sh start <ticket-name>` - Start working on ticket (creates or switches to feature branch)
- `bash ./scripts/ticket.sh restore` - Restore current-ticket.md symlink from branch name
- `bash ./scripts/ticket.sh check` - Check current directory and ticket/branch synchronization status
- `bash ./scripts/ticket.sh close [--no-push] [--force|-f] [--no-delete-remote]` - Complete current ticket (squash merge to default branch)
- `bash ./scripts/ticket.sh selfupdate` - Update ticket.sh to the latest version from GitHub
- `bash ./scripts/ticket.sh version` - Display version information
- `bash ./scripts/ticket.sh prompt` - Display prompt instructions for AI coding assistants

## Ticket Naming

- Format: `YYMMDD-hhmmss-<slug>`
- Example: `241225-143502-implement-user-auth`
- Generated automatically when creating tickets

## Ticket Status

- `todo`: not started (started_at: null)
- `doing`: in progress (started_at set, closed_at: null)
- `done`: completed (closed_at set)

## Configuration

- Config file: `.ticket-config.yaml` or `.ticket-config.yml` (in project root)
- Initialize with: `bash ./scripts/ticket.sh init`
- Edit to customize directories, branches, templates, and success messages

### Success Messages

- `new_success_message`: Displayed after creating a new ticket
- `start_success_message`: Displayed after starting work on a ticket
- `restore_success_message`: Displayed after restoring current ticket link
- `close_success_message`: Displayed after closing a ticket
- All messages default to empty (disabled) and support multiline YAML format

## Push Control

- Set `auto_push: false` in config to disable automatic pushing for close command
- Use `--no-push` flag with close command to skip pushing
- Feature branches are always created locally (no auto-push on start)
- Git commands and outputs are displayed for transparency

## Workflow

### Create New Ticket

1. Create ticket: `bash ./scripts/ticket.sh new feature-name`
2. Edit ticket content and description in the generated file

### Start Work

1. Check available tickets: `bash ./scripts/ticket.sh list` or browse tickets directory
2. Start work: `bash ./scripts/ticket.sh start 241225-143502-feature-name`
3. Develop on feature branch (`current-ticket.md` shows active ticket)

### Closing

1. Before closing:
   - Review ticket content and description
   - Check all tasks in checklist are completed (mark with `[x]`)
   - Get user approve before proceeding
2. Complete: `bash ./scripts/ticket.sh close`

**Note**: If specific workflow instructions are provided elsewhere (e.g., in project documentation or CLAUDE.md), those take precedence over this general workflow.

## Troubleshooting

- Run from project root (where `.git` and config file exist)
- Use `restore` if `current-ticket.md` is missing after clone/pull
- Check `list` to see available tickets and their status
- Ensure Git working directory is clean before start/close

**Note**: `current-ticket.md` is git-ignored and needs `restore` after clone/pull.

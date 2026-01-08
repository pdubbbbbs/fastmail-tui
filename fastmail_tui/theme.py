"""IlluminatiNebula theme - colors, icons, and Textual CSS."""

from rich.theme import Theme

# IlluminatiNebula color palette
COLORS = {
  "primary": "#00D4FF",       # Cyan accent
  "secondary": "#9945FF",     # Purple
  "tertiary": "#FF6B35",      # Orange accent
  "background": "#0A0A0F",    # Deep dark
  "panel_bg": "#12121A",      # Panel background
  "surface": "#1A1A24",       # Elevated surface
  "foreground": "#E0E0E0",    # Main text
  "muted": "#666688",         # Muted text
  "success": "#00FF88",       # Green
  "error": "#FF4444",         # Red
  "warning": "#FFB800",       # Yellow/Orange
  "border": "#2A2A3A",        # Border color
  "highlight": "#00D4FF33",   # Selection highlight (with alpha)
  "unread": "#00D4FF",        # Unread indicator
  "starred": "#FFD700",       # Gold star
  "encrypted": "#00FF88",     # Green for secure
  "ai": "#9945FF",            # AI/magic purple
}

# Unicode icons for the UI
ICONS = {
  # Mailboxes
  "inbox": "",
  "sent": "",
  "drafts": "",
  "trash": "",
  "archive": "",
  "spam": "",
  "folder": "",
  "folder_open": "",

  # Email status
  "starred": "",
  "unread": "",
  "read": "",
  "attachment": "",
  "encrypted": "",
  "flagged": "",

  # Actions
  "reply": "",
  "reply_all": "",
  "forward": "",
  "delete": "",
  "archive_action": "",
  "compose": "",

  # Features
  "masked": "",         # Masked email (privacy)
  "ai": "",             # AI/magic
  "search": "",
  "filter": "",

  # Status
  "loading": "",
  "sync": "",
  "error": "",
  "success": "",
  "warning": "",
  "connected": "",
  "disconnected": "",

  # Navigation
  "chevron_right": "",
  "chevron_down": "",
  "arrow_up": "",
  "arrow_down": "",
}

# Rich theme for console output
RICH_THEME = Theme({
  "primary": f"bold {COLORS['primary']}",
  "secondary": f"{COLORS['secondary']}",
  "success": f"bold {COLORS['success']}",
  "error": f"bold {COLORS['error']}",
  "warning": f"bold {COLORS['warning']}",
  "muted": f"{COLORS['muted']}",
  "info": f"{COLORS['primary']}",
})

# Textual CSS for the application
TEXTUAL_CSS = """
/* Global styles */
Screen {
  background: #0A0A0F;
}

/* Header styling */
Header {
  background: #12121A;
  color: #00D4FF;
  text-style: bold;
}

/* Footer styling */
Footer {
  background: #12121A;
}

FooterKey > .footer-key--key {
  background: #00D4FF;
  color: #0A0A0F;
}

FooterKey > .footer-key--description {
  color: #E0E0E0;
}

/* Container layouts */
#main {
  height: 100%;
  width: 100%;
}

#content {
  height: 100%;
}

/* Mailbox tree (left sidebar) */
#mailbox-tree {
  width: 25;
  min-width: 20;
  max-width: 35;
  background: #12121A;
  border-right: solid #2A2A3A;
  padding: 1;
}

#mailbox-tree .tree--label {
  color: #E0E0E0;
}

#mailbox-tree .tree--cursor {
  background: #00D4FF33;
}

#mailbox-tree .tree--highlight {
  background: #00D4FF22;
}

/* Email area (center) */
#email-area {
  width: 1fr;
}

/* Email list */
#email-list {
  height: 60%;
  background: #12121A;
  border-bottom: solid #2A2A3A;
}

#email-list DataTable {
  height: 100%;
}

#email-list DataTable > .datatable--cursor {
  background: #00D4FF33;
}

#email-list DataTable > .datatable--header {
  background: #1A1A24;
  color: #00D4FF;
  text-style: bold;
}

/* Email preview */
#email-preview {
  height: 40%;
  background: #0A0A0F;
  padding: 1;
  overflow-y: auto;
}

#email-preview .email-header {
  color: #00D4FF;
  text-style: bold;
  margin-bottom: 1;
}

#email-preview .email-meta {
  color: #666688;
  margin-bottom: 1;
}

#email-preview .email-body {
  color: #E0E0E0;
}

/* AI panel (right sidebar) */
#ai-panel {
  width: 30;
  min-width: 25;
  max-width: 40;
  background: #12121A;
  border-left: solid #2A2A3A;
  padding: 1;
}

#ai-panel .title {
  color: #9945FF;
  text-style: bold;
  margin-bottom: 1;
}

#ai-panel .summary {
  color: #E0E0E0;
  margin-bottom: 1;
}

#ai-panel .action-item {
  color: #00FF88;
}

/* Status bar */
#status-bar {
  height: 1;
  background: #1A1A24;
  color: #666688;
  padding: 0 1;
}

#status-bar .connected {
  color: #00FF88;
}

#status-bar .syncing {
  color: #00D4FF;
}

#status-bar .error {
  color: #FF4444;
}

/* Panel titles */
.title {
  background: #1A1A24;
  color: #00D4FF;
  text-style: bold;
  padding: 0 1;
  margin-bottom: 1;
}

/* DataTable general */
DataTable {
  background: #12121A;
}

DataTable > .datatable--cursor {
  background: #00D4FF33;
}

DataTable > .datatable--hover {
  background: #00D4FF11;
}

/* Input fields */
Input {
  background: #0A0A0F;
  border: solid #2A2A3A;
  padding: 0 1;
}

Input:focus {
  border: solid #00D4FF;
}

Input > .input--placeholder {
  color: #666688;
}

/* Buttons */
Button {
  background: #00D4FF;
  color: #0A0A0F;
  border: none;
  padding: 0 2;
}

Button:hover {
  background: #33DDFF;
}

Button:focus {
  border: solid #9945FF;
}

Button.-primary {
  background: #00D4FF;
}

Button.-secondary {
  background: #9945FF;
}

Button.-error {
  background: #FF4444;
}

/* Modal screens */
ModalScreen {
  background: #0A0A0F88;
}

/* Modals/dialogs */
.modal-container {
  background: #12121A;
  border: solid #00D4FF;
  padding: 1 2;
  width: 60;
  height: auto;
}

.modal-title {
  color: #00D4FF;
  text-style: bold;
  text-align: center;
  margin-bottom: 1;
}

/* Search modal */
#search-modal {
  align: center middle;
}

#search-modal .results {
  height: 20;
  overflow-y: auto;
  margin-top: 1;
}

#search-modal .result-item {
  padding: 0 1;
}

#search-modal .result-item:hover {
  background: #00D4FF33;
}

/* Email status indicators */
.unread {
  text-style: bold;
  color: #00D4FF;
}

.starred {
  color: #FFD700;
}

.has-attachment {
  color: #9945FF;
}

/* Masked email panel */
#masked-email-panel .masked-active {
  color: #00FF88;
}

#masked-email-panel .masked-disabled {
  color: #FF4444;
}

/* Compose modal */
#compose-modal {
  align: center middle;
}

#compose-modal .compose-container {
  width: 80%;
  height: 80%;
  background: #12121A;
  border: solid #00D4FF;
  padding: 1;
}

#compose-modal TextArea {
  height: 1fr;
  background: #0A0A0F;
  border: solid #2A2A3A;
}

#compose-modal TextArea:focus {
  border: solid #00D4FF;
}

/* Setup screen */
#setup-screen {
  align: center middle;
}

#setup-screen .setup-container {
  width: 60;
  background: #12121A;
  border: solid #00D4FF;
  padding: 2;
}

#setup-screen .setup-title {
  color: #00D4FF;
  text-style: bold;
  text-align: center;
  margin-bottom: 2;
}

#setup-screen .setup-label {
  color: #E0E0E0;
  margin-top: 1;
}

#setup-screen .setup-hint {
  color: #666688;
  margin-bottom: 1;
}

/* Toast notifications */
Toast {
  background: #1A1A24;
  border: solid #2A2A3A;
  padding: 1 2;
}

Toast.-information {
  border-left: wide #00D4FF;
}

Toast.-success {
  border-left: wide #00FF88;
}

Toast.-error {
  border-left: wide #FF4444;
}

Toast.-warning {
  border-left: wide #FFB800;
}

/* Loading indicator */
LoadingIndicator {
  color: #00D4FF;
}

/* Progress bar */
ProgressBar > .bar--bar {
  color: #00D4FF;
}

ProgressBar > .bar--complete {
  color: #00FF88;
}

/* Scrollbar styling */
Scrollbar {
  background: #1A1A24;
}

Scrollbar > .scrollbar--scroll {
  background: #2A2A3A;
}

Scrollbar:hover > .scrollbar--scroll {
  background: #00D4FF;
}
"""

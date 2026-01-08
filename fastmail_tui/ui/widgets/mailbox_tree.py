"""Mailbox tree widget for folder navigation."""

from typing import Optional, List
from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from textual.message import Message
from rich.text import Text

from ...models.mailbox import Mailbox
from ...theme import COLORS, ICONS


class MailboxTree(Tree):
  """Tree widget for mailbox/folder navigation.

  Displays mailboxes in a hierarchical tree with icons,
  unread counts, and selection support.
  """

  class MailboxSelected(Message):
    """Message emitted when a mailbox is selected."""

    def __init__(self, mailbox: Mailbox) -> None:
      self.mailbox = mailbox
      super().__init__()

  DEFAULT_CSS = """
  MailboxTree {
    width: 25;
    min-width: 20;
    max-width: 35;
    background: #12121A;
    border-right: solid #2A2A3A;
    padding: 1;
  }

  MailboxTree > .tree--label {
    color: #E0E0E0;
  }

  MailboxTree > .tree--cursor {
    background: #00D4FF33;
  }

  MailboxTree > .tree--highlight {
    background: #00D4FF22;
  }

  MailboxTree > .tree--guides {
    color: #2A2A3A;
  }
  """

  def __init__(
    self,
    mailboxes: Optional[List[Mailbox]] = None,
    **kwargs,
  ):
    """Initialize mailbox tree.

    Args:
      mailboxes: Initial list of mailboxes to display
    """
    super().__init__(
      label=Text(f" {ICONS['inbox']} MAILBOXES", style=f"bold {COLORS['primary']}"),
      **kwargs,
    )
    self._mailboxes: dict[str, Mailbox] = {}
    self._nodes: dict[str, TreeNode] = {}

    if mailboxes:
      self.update_mailboxes(mailboxes)

  def update_mailboxes(self, mailboxes: List[Mailbox]) -> None:
    """Update the tree with new mailbox data.

    Args:
      mailboxes: List of Mailbox objects to display
    """
    self._mailboxes.clear()
    self._nodes.clear()
    self.root.remove_children()

    # First pass: create nodes for all mailboxes
    for mailbox in mailboxes:
      self._mailboxes[mailbox.id] = mailbox

    # Build tree structure
    for mailbox in mailboxes:
      self._add_mailbox_node(mailbox)

    # Expand root by default
    self.root.expand()

  def _add_mailbox_node(self, mailbox: Mailbox) -> TreeNode:
    """Add a mailbox node to the tree.

    Args:
      mailbox: Mailbox to add

    Returns:
      The created TreeNode
    """
    if mailbox.id in self._nodes:
      return self._nodes[mailbox.id]

    # Build the label
    label = self._build_mailbox_label(mailbox)

    # Find parent node
    parent_node = self.root
    if mailbox.parent_id and mailbox.parent_id in self._mailboxes:
      parent = self._mailboxes[mailbox.parent_id]
      if parent.id not in self._nodes:
        # Recursively add parent first
        parent_node = self._add_mailbox_node(parent)
      else:
        parent_node = self._nodes[parent.id]

    # Add the node
    node = parent_node.add(label, data=mailbox)
    self._nodes[mailbox.id] = node

    return node

  def _build_mailbox_label(self, mailbox: Mailbox) -> Text:
    """Build the display label for a mailbox.

    Args:
      mailbox: Mailbox to build label for

    Returns:
      Rich Text object with styled label
    """
    label = Text()

    # Icon
    label.append(f"{mailbox.icon} ", style=COLORS["muted"])

    # Name
    name_style = COLORS["foreground"]
    if mailbox.unread_emails > 0:
      name_style = f"bold {COLORS['primary']}"

    label.append(mailbox.display_name, style=name_style)

    # Unread count
    if mailbox.unread_emails > 0:
      label.append(f" ({mailbox.unread_display})", style=f"bold {COLORS['unread']}")

    return label

  def refresh_mailbox(self, mailbox: Mailbox) -> None:
    """Refresh a single mailbox's display.

    Args:
      mailbox: Updated mailbox data
    """
    self._mailboxes[mailbox.id] = mailbox

    if mailbox.id in self._nodes:
      node = self._nodes[mailbox.id]
      node.set_label(self._build_mailbox_label(mailbox))

  def select_mailbox(self, mailbox_id: str) -> None:
    """Select a mailbox by ID.

    Args:
      mailbox_id: ID of mailbox to select
    """
    if mailbox_id in self._nodes:
      self.select_node(self._nodes[mailbox_id])

  def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
    """Handle node selection."""
    if event.node.data and isinstance(event.node.data, Mailbox):
      self.post_message(self.MailboxSelected(event.node.data))

  def get_selected_mailbox(self) -> Optional[Mailbox]:
    """Get the currently selected mailbox.

    Returns:
      Selected Mailbox or None
    """
    if self.cursor_node and self.cursor_node.data:
      return self.cursor_node.data
    return None

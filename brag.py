#!/usr/bin/env python3
# coding=utf-8
"""
BragMaster 3000
"""
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from enum import Enum
import re
import os
import sys
from datetime import datetime
import argparse
import tempfile
import subprocess
import shlex

__author__ = "Manuel Ebert"
__copyright__ = "Copyright 2016, Manuel Ebert"
__date__ = "2016-02-22"
__email__ = "manuel@1450.me"
__version__ = "0.1.0"


def parse_sections(text, separator):
    """Separates a text into sections. For example,

        # Header 1
        Text
        # Header 2
        More text

    can be separated into sections with get_sections(text, "^# ")

    Args:
      text: str
      separator: regular expression
    Returns:
      generator
    """
    section_starts = [m.start() for m in re.finditer(separator, text, flags=re.MULTILINE)]
    for start, end in zip(section_starts, section_starts[1:] + [len(text)]):
        yield text[start:end]


def get_text_from_editor(editor='vim', template=""):
    """Opens an editor, prefills it with a template, and returns the edited text.

    Args:
        editor: str -- command to open the editor, eg. 'vim'
        template: str
    Returns:
        str
    """
    filehandle, tmpfile = tempfile.mkstemp(prefix="brag", text=True, suffix=".md")
    with open(tmpfile, 'w', encoding="utf-8") as f:
        if template:
            f.write(template)
    subprocess.call(shlex.split(editor, posix="win" not in sys.platform) + [tmpfile])
    with open(tmpfile, encoding="utf-8") as f:
        result = f.read()
    os.close(filehandle)
    os.remove(tmpfile)
    return result


class Status(Enum):
    """Status of a task"""

    done = 'X'
    incomplete = ' '
    partial = 'O'

    @classmethod
    def from_string(cls, text):
        """Generates a new staus from a string ('x', 'o', or ' ')"""
        if not text:
            return cls(' ')
        else:
            return cls(text.upper())

    def __str__(self):
        """Returns the symbol for the status"""
        return self.value

    def __bool__(self):
        """Returns True if the status is not incomplete."""
        return self.value != ' '


class Task(object):
    """Task object"""

    DONE = 1
    INCOMPLETE = 0
    PARTIAL = 2

    def __init__(self, name, status, comment=""):
        """Initialises the task.

        Args:
            name: str
            status: str or Status
            comment: str
        """
        self.name = name
        self.status = Status.from_string(status) if not isinstance(status, Status) else status
        self.comment = comment

    def __bool__(self):
        """Returns true if the task is completed."""
        return self.status == Status.done

    def update(self, other_task):
        """Updates the comment and status from another task."""
        self.status = other_task.status
        self.comment = other_task.comment

    @classmethod
    def from_string(cls, line):
        """Parse a string and return the status. Examples:

        - [X] Wear underwear
        - [ ] Wear pants
        - [O] Wear socks -- Didn't match, but ok
        - Pretend being adult
        1. [X] Collect socks
        2. ???
        * Profit!!!
        """
        try:
            status, name, comment = re.match("^ *(?:[-*]|[0-9]+\.) (?:\[(.)\] +)?(?:(.*(?= -- | — )|.*)(?: -- | — )?(.*))", line).groups()
        except:
            return None
        if name == "...":
            return None
        return cls(name, status, comment.strip())

    def __str__(self):
        """Returns a Markdown list item representation of the task."""
        return self.to_string()

    def to_string(self, simple=False):
        """Returns a Markdown list item representation of the task.

        Args:
            simple: bool -- If True, omits checkboxes for unfinished tasks
        Returns:
            str
        """
        if simple and not self.status:
            result = "- {}".format(self.name)
        else:
            result = "- [{}] {}".format(self.status, self.name)

        if self.comment:
            result += " -- " + self.comment
        return result

    def __repr__(self):
        """Returns a string representation of the task."""
        return "<[{}] {}>".format(self.status, self.name)

    def __eq__(self, other):
        """True if names match"""
        return self.name == other.name


class Session(object):
    """Session object. Contains task."""

    def __init__(self, name, tasks=None):
        """Initialises the session with a name and task list."""
        try:
            self.date = datetime.strptime(name.strip(), "%Y-%m-%d")
        except:
            self.date = None
        self.name = "Goals" if "goals" in name.lower() else name.strip()
        self.tasks = tasks or []

    @classmethod
    def from_string(cls, section_string):
        """Parses the session from a markdown string.
        The first line should contain the session name, subsequent lines a list of tasks.
        """
        title, items = section_string.strip("# ").split("\n", 1)
        items = filter(
            lambda i: i is not None,
            map(
                Task.from_string,
                re.findall(r"^ *(?:[-*]|[0-9]+\.) .*", items, re.MULTILINE)
            )
        )
        if not items:
            return None
        return Session(title, list(items))

    def __eq__(self, other):
        """True if names match"""
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name

    def __lt__(self, other):
        """Compares the date of session."""
        if not self.date or not other.date:
            return False
        return self.date < other.date

    def __str__(self):
        """Returns a Markdown representation of the session."""
        tasks = "\n".join(map(str, self.tasks))
        return "## {}\n\n{}".format(self.name, tasks)

    def __len__(self):
        """Returns the number of tasks in this session."""
        return len(self.tasks)

    def get_unfinished(self):
        """Returns a new session with only the unfinished tasks of this session."""
        return Session(self.name, filter(lambda t: not t, self.tasks))

    def __iter__(self):
        """Returns a generator that yields tasks."""
        for task in self.tasks:
            yield task

    def get_task(self, name):
        """Finds a task by name"""
        for task in self:
            if task.name == name:
                return task

    def update(self, other_session):
        """Updates or adds new tasks from another session."""
        for task in other_session:
            if task not in self:
                self.tasks.append(task)
            else:
                self.get_task(task.name).update(task)

    def to_string(self, simple=False, title=True):
        """Returns a Markdown representatino of the session.

        Args:
            title: bool -- If True, include header for this session
            simple: bool -- If True, omits checkboxes for unfinished tasks
        Returns:
            str
        """
        result = "## {}\n\n".format(self.name) if title else ""
        result += "\n".join([task.to_string(simple=simple) for task in self.tasks])
        return result


class User(object):
    """User Object"""

    def __init__(self, name, goals, sessions, email=None):
        """Initialises a new user."""
        self.name = name
        self.goals = goals
        self.sessions = sessions
        self.email = email

    def __str__(self):
        """Returns a string representation of the user and their email."""
        return "{} <{}>".format(self.name, self.email or "")

    def __eq__(self, other):
        """True if names match"""
        return self.name.lower() == other.name.lower()

    def get_last_session(self):
        """Returns the last (completed) session."""
        return sorted(self.sessions)[-2]

    def get_current_session(self):
        """Returns the current (ongoing) session."""
        return sorted(self.sessions)[-1]

    def get_session(self, date):
        """Finds a session by date."""
        for session in self.sessions:
            if date == session.date:
                return session

    def name_and_email(self):
        """Returns a string representation of the user's name and email (if available)"""
        return self.name if not self.email else "{} <{}>".format(self.name, self.email)

    def to_string(self):
        """Returns a Markdown representation of all of the user's sessions."""
        result = "# {}\n\n{}\n\n".format(self.name_and_email(), self.goals)
        result += "\n\n".join(map(str, sorted(self.sessions)))
        return result

    def stats(self):
        """Returns statistics on the user.

        Returns:
            dict
        """
        tasks_completed = sum([len([t for t in session if t]) for session in self.sessions])
        tasks_missed = sum([len([t for t in session if not t]) for session in self.sessions[:-1]])
        return {
            'Sessions': len(self.sessions),
            'Goals completed': len([t for t in self.goals if t]),
            'Total tasks': sum([len(session) for session in self.sessions]),
            'Tasks in progress': len(self.sessions[-1]),
            'Tasks completed': tasks_completed,
            'Tasks missed': tasks_missed,
            'Ratio': tasks_completed / (tasks_completed + tasks_missed)
        }


class Brag(object):
    """Brag object. Contains users, each having goals and sessions, each session containing tasks."""

    def __init__(self):
        """Initialises the Brag."""
        self.users = []
        self.filename = None

    def add_user(self, user):
        """Adds a new user to the Brag"""
        self.users.append(user)

    def get_user(self, username):
        """Finds a user by their name."""
        for user in self.users:
            if user.name.lower() == username.lower():
                return user

    @property
    def current_session(self):
        """Returns the current (ongoing) session"""
        if not self.get_session_dates():
            return None
        return self.get_session_dates()[-1]

    @property
    def last_session(self):
        """Returns the last (completed) session"""
        if not self.get_session_dates():
            return None
        return self.get_session_dates()[-2]

    def session_to_string(self, date, title=True, simple=False):
        """Turns a single session into markdown

        Args:
            date: datetime -- Session date
            title: bool -- If True, include header for this session
            simple: bool -- If True, omits checkboxes for unfinished tasks
        Returns:
            str
        """
        result = ""
        for user in self.users:
            session = user.get_session(date)
            if session:
                result += "# {}\n\n{}\n\n".format(user.name, session.to_string(title=title, simple=simple))
        return result.strip()

    def to_string(self):
        """Returns a markdown file for this Brag

        Returns:
            str
        """
        sep = "\n\n" + "-" * 60 + "\n\n"
        return sep.join([u.to_string() for u in self.users])

    def get_session_template(self):
        """Generates a template with which the Brag can be updated.
        For each user, list their goals, last session's tasks, and a stub
        for the current session.

        Returns:
            str
        """
        result = ""
        last_session = max(self.get_session_dates())
        for user in self.users:
            result += "# {}\n\n".format(user.name)
            result += user.goals.get_unfinished().to_string(simple=True) + "\n\n"
            result += str(user.get_session(last_session)) + "\n\n"
            result += "## {:%Y-%m-%d}\n\n- ...\n\n".format(datetime.now())
            result += "-" * 60 + "\n\n"
        return result.strip()

    def get_session_dates(self):
        """Returns the dates of all sessions.

        Returns:
            list -- list of dates.
        """
        sessions = set()
        for user in self.users:
            for session in user.sessions:
                sessions.add(session.date)
        return sorted(list(sessions))

    @classmethod
    def from_file(cls, filename):
        """Parses a markdown file into a brag.

        Returns:
            Brag
        """
        filename = os.path.expanduser(filename)
        with open(filename, encoding='utf-8') as f:
            brag = cls.from_string(f.read())
        brag.filename = filename
        return brag

    @classmethod
    def from_string(cls, brag_string):
        """Parses a markdown string into a brag.

        Returns:
            Brag
        """
        brag = cls()
        for part in parse_sections(brag_string, r'^# '):
            header, rest = part.split("\n", 1)
            username, email = re.match(r"[# ]*([^<]+)(?: *<)?([^>]+)?(?:> *)?", header).groups()
            sessions = []
            goals = None
            for section in parse_sections(rest, r'^## '):
                session = Session.from_string(section)
                if "goals" in session.name.lower():
                    goals = session
                elif session:
                    sessions.append(session)
            brag.add_user(User(username.strip(), goals, sessions, email))
        return brag

    def update(self, other_brag):
        """Updates from another brag."""
        for other_user in other_brag.users:
            if other_user not in self.users:
                self.add_user(other_user)
            else:
                my_user = self.users[self.users.index(other_user)]
                my_user.goals.update(other_user.goals)
                for session in other_user.sessions:
                    if session not in my_user.sessions:
                        my_user.sessions.append(session)
                    else:
                        my_user.get_session(session.date).update(session)

    def write(self):
        """Saves the brag to file."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(self.to_string())

if __name__ == "__main__":
    brag_file = os.environ.get('BRAG_FILE', None)
    brag_editor = os.environ.get('BRAG_EDITOR', 'vim')
    commands = {
        'current': "Displays this week's tasks",
        'last': "Displays last week's tasks",
        'stats': "Displays some statistics",
        'users': "Displays all users and their email addresses",
        'run': "Runs a brag session by opening the editor with a template"
    }

    command_descriptions = '\n'.join(["  {} - {}".format(k, v) for k, v in commands.items()])

    parser = argparse.ArgumentParser(
        prog='brag',
        usage='%(prog)s COMMAND [options]',
        description="""Business Re-Evaluation and Enhancement Group helper. Available commands are: \n\n""" + command_descriptions,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('command', help='command to run', metavar='COMMAND', choices=commands.keys())
    parser.add_argument('-f', dest='file', default=brag_file, help='path to brag file', required=not brag_file)
    parser.add_argument('-e', dest='editor', default=brag_editor, help='editor to use for running brag')
    parser.add_argument('-u', dest='users', help='filter by users, separate multiple users with commas.')
    parser.add_argument('-i', dest='input', help='input file')
    args = parser.parse_args()

    brag = Brag.from_file(args.file)

    if args.users:
        usernames = args.users.lower().split(",")
        brag.users = [u for u in brag.users if u.name.lower() in usernames]
        brag_usernames = [u.name.lower() for u in brag.users]
        for username in usernames:
            if username not in brag_usernames:
                print("\033[93mUser '{}' not found.\033[0m".format(username))

    if args.command == "current":
        print(brag.session_to_string(
            brag.current_session,
            title=False, simple=True)
        )
    if args.command == "last":
        print(brag.session_to_string(brag.last_session, title=False))

    elif args.command == "users":
        print(", ".join(map(str, brag.users)))

    elif args.command == "stats":
        usernames = [user.name for user in brag.users]
        username_lengths = map(len, usernames)
        user_stats = [user.stats() for user in brag.users]
        keys = user_stats[0].keys()
        longest_key = max(map(len, keys))
        print("{} {}  Total".format(" " * longest_key, "  ".join(usernames)))
        zipped = list(zip(user_stats, username_lengths))
        for key in sorted(keys):
            total = sum(stats[key] for stats in user_stats)
            frmt = "{:{}.0%}" if key == "Ratio" else "{:>{}}"
            if key == "Ratio":
                total = total / len(brag.users)
            formatted_stats = "  ".join([frmt.format(stats[key], length) for stats, length in zipped])
            formatted_stats += frmt.format(total, 7)
            print("{:{}} {}".format(key, longest_key, formatted_stats))

    elif args.command == "run":
        new_brag = get_text_from_editor(
            editor=args.editor,
            template=brag.get_session_template()
        )
        new_brag = Brag.from_string(new_brag)

        brag_with_all_users = Brag.from_file(args.file)
        brag_with_all_users.update(new_brag)
        brag_with_all_users.write()

#!/usr/bin/env python3
# coding=utf-8
"""
BragMaster 3000
"""
from __future__ import unicode_literals
from __future__ import absolute_import

from enum import Enum
import re
import os
import sys
from datetime import datetime
import argparse

__author__ = "Manuel Ebert"
__copyright__ = "Copyright 2016, Manuel Ebert"
__date__ = "2016-02-22"
__email__ = "manuel@1450.me"
__version__ = "0.1.0"


class Status(Enum):
    done = 'X'
    incomplete = ' '
    partial = 'O'

    def __str__(self):
        return self.value

    def __bool__(self):
        return self.value != ' '


class Task(object):
    DONE = 1
    INCOMPLETE = 0
    PARTIAL = 2

    def __init__(self, name, status, comment):
        self.name = name
        self.status = status
        self.comment = comment

    def update(self, other_task):
        self.status = other_task.status
        self.comment = other_task.comment

    @classmethod
    def from_string(cls, line):
        line = line.replace("—", "--")  # Long dashes
        line, comment = line.split("--", 1) if "--" in line else (line, "")
        line = line.strip("- ")
        if line.startswith("["):
            status = Status(line[1].upper())
            name = line[3:].strip()
        else:
            status = Status.incomplete
            name = line

        return cls(name, status, comment.strip())

    def __str__(self):
        return self.to_string()

    def to_string(self, simple=False):
        if simple:
            result = "- {}".format(self.name)
        else:
            result = "- [{}] {}".format(self.status, self.name)

        if self.comment:
            result += " -- " + self.comment
        return result

    def __repr__(self):
        return "<[{}] {}>".format(self.status, self.name)

    def __eq__(self, other):
        return self.name == other.name


class Session(object):
    def __init__(self, name, tasks=None):
        try:
            self.date = datetime.strptime(name.strip(), "%Y-%m-%d")
        except:
            self.date = None
        self.name = "Goals" if "goals" in name.lower() else name.strip()
        self.tasks = tasks or []

    @classmethod
    def from_string(cls, section_string):
        title, items = section_string.split("\n", 1)
        items = map(Task.from_string,
                    filter(lambda line: line.strip() and not line.strip().startswith("---"),
                           items.strip().splitlines()))

        return Session(title, list(items))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name

    def __lt__(self, other):
        if not self.date or not other.date:
            return False
        return self.date < other.date

    def __str__(self):
        tasks = "\n".join(map(str, self.tasks))
        return "## {}\n\n{}".format(self.name, tasks)

    def get_unfinished(self):
        return Session(self.name, filter(bool, self.tasks))

    def __iter__(self):
        yield from self.tasks

    def get_task(self, name):
        for task in self:
            if task.name == name:
                return task

    def update(self, other_session):
        for task in other_session:
            if task not in self:
                self.tasks.append(task)
            else:
                self.get_task(task.name).update(task)

    def to_string(self, simple=False, title=True):
        result = "## {}\n\n".format(self.name) if title else ""
        result += "\n".join([task.to_string(simple=simple) for task in self.tasks])
        return result


class User(object):
    def __init__(self, name, goals, sessions, email=None):
        self.name = name
        self.goals = goals
        self.sessions = sessions
        self.email = email

    def __str__(self):
        return "{} <{}>".format(self.name, self.email or "")

    def __eq__(self, other):
        return self.name.lower() == other.name.lower()

    def get_last_session(self):
        return sorted(self.sessions)[-2]

    def get_current_session(self):
        return sorted(self.sessions)[-1]

    def get_session(self, date):
        for session in self.sessions:
            if date == session.date:
                return session

    def name_and_email(self):
        return self.name if not self.email else "{} <{}>".format(self.name, self.email)

    def to_string(self):
        result = "# {}\n\n{}\n\n".format(self.name_and_email(), self.goals)
        result += "\n\n".join(map(str, sorted(self.sessions)))
        return result


class Brag(object):
    def __init__(self):
        self.users = []
        self.filename = None

    def add_user(self, user):
        self.users.append(user)
    
    def get_user(self, username):
        for user in self.users:
            if user.name.lower() == username.lower():
                return user

    def get_current_session(self):
        current_session = max(self.get_session_names())
        return self.get_session(current_session)

    def get_last_session(self):
        last_session = self.get_session_names()[-2]
        return self.get_session(last_session)

    def get_session(self, date):
        result = ""
        for user in self.users:
            user_session = user.get_session(date)
            if user_session:
                result += "# {}\n\n{}\n\n".format(user.name, user_session)
        return result.strip()

    def get_all_sessions(self):
        sep = "\n\n" + "-" * 60 + "\n\n"
        return sep.join([u.to_string() for u in self.users])

    def get_session_template(self):
        result = ""
        last_session = max(self.get_session_names())
        for user in self.users:
            result += "# {}\n\n".format(user.name)
            result += user.goals.get_unfinished().to_string(simple=True) + "\n\n"
            result += str(user.get_session(last_session)) + "\n\n"
            result += "## {:%Y-%m-%d}\n\n- ...\n\n".format(datetime.now())
            result += "-" * 60 + "\n\n"
        return result.strip()

    def get_session_names(self):
        sessions = set()
        for user in self.users:
            for session in user.sessions:
                sessions.add(session.date)
        return sorted(list(sessions))

    @classmethod
    def from_file(cls, filename):
        # Parse file
        with open(os.path.expanduser(filename), encoding='utf-8') as f:
            brag = cls.from_string(f.read())
        brag.filename = filename
        return brag

    @classmethod
    def from_string(cls, brag_string):
        brag = cls()
        parts = re.split(r"^# ", brag_string, flags=re.MULTILINE)
        for part in parts:
            if not part:
                continue
            username, part = part.split("\n", 1)
            email = None
            if "<" in username:
                username, email = re.match(r"([^<]+) +<([^>]+)>", username.strip()).groups()
            sections = re.split(r"^## ", part, flags=re.MULTILINE)
            sessions = []
            goals = []
            for section in sections:
                if not section.strip():
                    continue
                session = Session.from_string(section)
                if "goals" in session.name.lower():
                    goals = session
                else:
                    sessions.append(session)
            brag.add_user(User(username, goals, sessions, email))
        return brag

    def update(self, other_brag):
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
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(self.get_all_sessions())

if __name__ == "__main__":
    commands = ['current', 'last', 'template', 'stats', 'users', 'update']
    brag_file = os.environ.get('BRAG_FILE', None)

    parser = argparse.ArgumentParser(description='Business Re-Evaluation and Enhancement Group helper')
    parser.add_argument('command', help='Command to run', metavar='COMMAND', choices=commands)
    parser.add_argument('-f', '--file', default=brag_file, help='Path to brag file', required=not brag_file)
    parser.add_argument('-w', '--write', action='store_true', help='Update brag file')
    parser.add_argument('-u', '--users', help='Filter by users, separate multiple users with commas.')
    parser.add_argument('-i', '--input', help='Input file')
    args = parser.parse_args()

    brag = Brag.from_file(args.file)

    if args.users:
        usernames = args.users.lower().split(",")
        brag.users = [u for u in brag.users if u.name.lower() in usernames]

    if args.command == "current":
        print(brag.get_current_session())
    if args.command == "last":
        print(brag.get_last_session())
    elif args.command == "template":
        print(brag.get_session_template())
    elif args.command == "users":
        print(", ".join(map(str, brag.users)))
    elif args.command == "update":
        if args.input:
            new_brag = Brag.from_file(args.input)
        else:
            new_brag = Brag.from_string(sys.stdin.read())
        brag.update(new_brag)
        if args.write:
            brag.write()
        else:
            print(brag.get_all_sessions())

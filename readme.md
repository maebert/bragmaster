# BRAGMaster 3000

BRAGMaster is a tool to help you facilitate Business Re-Evaluation and Enhancement Groups (BRAGs).

![Bragging](http://i.giphy.com/xT77Y5UUIdbefJL0PK.gif)

To use a BRAGMaster, you need a BRAG file. The BRAG file is a simple markdown file. Each top-level header (`#`) seperates the the section for one user (the email address is optional). Each user has a Goals section (`## Goals`) that contains their medium term life and career goals. Each BRAG session is another section under the users. Tasks marked with [X] completed. Everything after `--` is a comment. Example:

```md
# Manuel <manuel@1450.me>

## Goals

- [ ] Run a marathon
- [ ] Make my company profitable

## 2016-02-06

- [X] Run 20k on the weekend -- Did it in 2:06:12
- [ ] Submit 5 pull requests

# Stan

....
```

## Usage

You either need to set the or supply a file with `-f path_to_brag_file` every time.

- `brag.py users`: Print all users and their e-mail addresses
- `brag.py current`: Print current tasks for everybody
- `brag.py last`: Print tasks for last brag for everybody
- `brag.py template`: Prints a template for running a BRAG session
- `brag.py update`: Update your brag file. Either specify a new bragfile with `-i filename` or pipe input into `brag.py`. Only new or changed tasks (change the status or add a comment) will be updated. 

Options:
- `-f path_to_brag_file` is required if you haven't set the  `$BRAG_FILE` environment variable (recommended)
- `-u name[,other_name]` limits the output to certain users
- `-w` write the output to the brag file. Only used for the `update` command.

## Updating a brag

The intended use is to use `brag.py template` to generate a template, and then update your brag file from that template. This snippet will open an editor with the  and automatically update the brag file, assuming `$BRAG_FILE` is set.

```sh
#!/bin/bash
tmpfile=$(mktemp /tmp/brag.XXXXXX)
brag.py template > $tmpfile
open -b pro.writer.mac -Wn $tmpfile
brag.py update -w < $tmpfile
rm $tmpfile
```

In this case, we use IA Writer (`open -b pro.writer.mac -Wn`). To use another editor, change this line to e.g.

- Sublime Text: `subl -w` (the `-w` flag prevents waits for the window to be closed before the script continues)
- vim: `vim`


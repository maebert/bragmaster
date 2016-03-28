# BRAGMaster 3000

BRAGMaster is a tool to help you facilitate Business Re-Evaluation and Enhancement Groups (BRAGs).

![Bragging](http://i.giphy.com/xT77Y5UUIdbefJL0PK.gif)

To use a BRAGMaster, you need a BRAG file. The BRAG file is a simple markdown file. Each top-level header (`#`) seperates the the section for one user (the email address is optional). Each user has a Goals section (`## Goals`) that contains their medium term life and career goals. Each BRAG session is another section under the users. Tasks marked with [X] completed. Everything after `--` is a comment. Example:

```md
# Manuel <manuel@1450.me>

## Goals

- [ ] Run a marathon
- [ ] Make my company profitable

## Recurring

- [ ] Meditate daily

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
- `brag.py run`: Runs a brag session

Options:
- `-f path_to_brag_file` is required if you haven't set the  `$BRAG_FILE` environment variable (recommended)
- `-u name[,other_name]` limits the output to certain users

## Running a brag session

```
brag.py run
```

You can specify the editor with the `-e` option or setting the `$BRAG_EDITOR` environment variable, e.g.

- IA Writer: `open -b pro.writer.mac -Wn`
- Sublime Text: `subl -w` (the `-w` flag prevents waits for the window to be closed before the script continues)
- vim: `vim`

## Sending automated reminders

`brag_mail.py` will use [Mandrill](http://www.mandrillapp.com) send an email to everyone to remind them of this week's task. To do this, you must set the `$MANDRILL_KEY` environment variable to your API key or pass it with the `-k` option.

```
Dear Manuel,

Today is Thursday, two more days to get your shit together and be productive. Gentle automated reminder, here are your tasks for this week:

- [ ] Run 20k on the weekend
- [ ] Submit 5 pull requests

This email was automatically generated by BRAGMaster 3000 - https://github.com/maebert/bragmaster
```

I recommend creating a crontab to do this automatically every Thursday at 9am:

```sh
0 9 * * 4 brag_mail.py -k YOUR_API_KEY -f YOUR_BRAG_FILE
```

## Managing Users

You can add `(inactive)` to the username in your brag file to keep them from showing up in `brag stats` and `brag run` like this:

```
# Manuel <manuel@1450.me> (inactive)
```



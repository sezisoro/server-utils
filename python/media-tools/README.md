# media-tools

Automation tools for downloading, organizing & tagging media via CLI

## Installation

`python3 -m pipx install -e .`

## media_organizer

Imagine this:

- You run a media server with limited time and resources, use deluge, are a
 strong seeder, and are a bit of a neat freak
- To keep seeding while importing media to your various servers, you use
 hardlinks to save space
- When a download completes, you need to verify if you've already imported the
 media, then link it and begin the triage process
- When a torrent needs to be removed, you again need to verify if it's been
 triaged yet

Instead of manually tracking what is ready for linking or deleting, always link
on download complete, always delete original on seeding complete.

The Deluge Execute plugin can trigger on these events. It is expected to call a
shell wrapper script with three arguments: `<torrent_id>` `<torrent_name>`
`<torrent_path>`. That script will call `organize_media` with `<torrent_path>`
so that the python script is still usable for ad-hoc runs.

See the [Deluge Execute docs](https://deluge-torrent.org/plugins/execute/) for
more information on hook integration. Unfortunately **it seems the Execute
plugin is broken, so all this is for nought**. Everntually I'll switch back to
`qbittorrent` and deal with the issues that comes with that software.

Anyway the program attempts to classify all files based on extensions (the
suffix from `pathlib.Path.suffix`), and then classify the whole download based
on what mediatypes are most common. If 70% are of one type, stamp the whole
thing as that type and then link it to the corresponding directory. The idea is
each broad category has it's own destination, triager or formatter, and server.

Later on I'll probably just switch to [MIME types](https://docs.python.org/3/library/mimetypes.html).

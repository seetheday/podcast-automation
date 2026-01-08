# Original manual workflow
The order is important

1. Record audio tracks as mono .WAV files on a Mac Mini.  One track for the host and one for the guest.
2. Sync the files to a Linux computer on the same network using Syncthing
3. Import tracks into Reaper by dragging and dropping.  Line both up to the left to ensure timing is aligned.
4. Normalize both tracks individually to -19 LUFS-I (not -16 because they're mono).
5. Trim the front of both tracks to when the podcast actually starts vs. the setup banter.
6. Group the two tracks and move them to the right to make room for intro music.
7. Drag intro music in from another tab in Reaper.  The intro music is already set up to be faded out after the first beat of the second measure.
8. Line up the start of the talking (usually "Hello") to the first beat of the 2nd measure of the intro music.
9. Apply Limiter to master (-1 db)
10. Apply noise gate to each track to cut out most quiet breath and mouth noises
11. Apply compressor to each track to make parts that are too quiet louder and parts that are too loud quieter.
12. Listen to podcast and cut out all: filler words, long pauses, repeated sentences (keeping the best one), breath noises that are still audible, mouth noises that are still audible, mouth clicks.
13. While listening and cutting out parts of the podcast, separate some of the overlapping voices where the guest and host talk over each other a lot (but not all because some overlap sounds natural).
14. Render as an MP3, ensuring that we remain at about LUFS-I -16 and about a -1 DB peak.  
15. Upload to Acast but don't publish yet.
16. Create episode image in GIMP based on a template and using relevant historical images (e.g. from Canadian archives or WikiMedia).
17. Write a good title for the podcast.
18. Upload episode image to Acast.
19. Schedule the podcast to be published on Acast.
20. Create an entry for the episode on the website via the Sanity headless CMS including a description, relevant metadata, and the uploaded episode image and schedule it to go live at the same time the episode is scheduled to go live on Acast.
21. Get the Acast ID from the Acast website about it, and enter that into the sanity headless cms entry before it goes live.

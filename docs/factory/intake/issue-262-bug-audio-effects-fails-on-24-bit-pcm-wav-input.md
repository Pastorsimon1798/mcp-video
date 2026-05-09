        # Factory intake for issue #262: Bug: audio_effects fails on 24-bit PCM WAV input

        Repository: `KyaniteLabs/mcp-video`
        Category: `llm_fix`
        Source issue: `#262`

        ## User request

        ## Bug Report

`audio_effects` fails with an internal error when processing WAV files recorded on macOS with 24-bit PCM audio.

This was found while dogfooding mcp-video on the Mac Mini for the EP01 social teaser workflow.

### Input

48kHz, 24-bit PCM WAV files recorded via ffmpeg/avfoundation:

```bash
ffmpeg -f avfoundation -i ":0" -ac 1 -ar 48000 -c:a pcm_s24le input.wav
```

### Error

The MCP tool returns:

```json
{"success":false,"error":{"type":"internal_error","code":"internal_error","message":"An internal error occurred. Check server logs for details."}}
```

### Expected behavior

`audio_effects` should apply requested effects such as reverb, normalize, compression, etc. and write a valid output file.

### Actual behavior

The tool fails with an internal error on the WAV input.

### Workaround used during dogfood

Processing the same files with ffmpeg directly using `-af` filters works:

```bash
ffmpeg -i input.wav -af "loudnorm=I=-14:TP=-2:LRA=11" output.wav
```

ffmpeg may emit warnings like:

```text
Decoding error: Invalid data found when processing input
corrupt input packet in stream 0
```

But ffmpeg still produces valid output. The likely issue is that the tool path does not robustly handle `pcm_s24le` / 24-bit PCM WAV input.

### Environment

- Machine: user's Mac Mini
- macOS Darwin 25.4.0
- ffmpeg 8.0 via Homebrew
- mcp-video latest at time of dogfood
- Input audio: 48kHz mono 24-bit PCM WAV (`pcm_s24le`)

        ## Factory interpretation

        This issue was picked up by `issue-closer`, but no safe code edit was
        produced by the configured agent providers. The Factory is therefore
        converting the issue into an implementation contract instead of silently
        skipping it.

        ## Acceptance contract

        - Confirm the desired behavior from the issue title and body.
        - Identify the smallest implementation slice that can ship independently.
        - Add or update tests/proofs for that slice before merging implementation.
        - Keep credentials, local machine paths, and deployment secrets out of the repo.
        - Close or update the source issue when the implementation PR lands.

        ## Next Factory action

        Dispatch a repo worker against this contract. If the request is too broad,
        split it into smaller `agent-ready` issues with concrete acceptance checks.

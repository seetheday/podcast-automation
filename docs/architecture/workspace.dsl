workspace "Podcast Automation" "C4 views that explain how the Maple History automation repo fits together." {
  model {
    producer = person "Podcast Producer" "Records Maple History episodes and runs the CLIs to push each stage forward."
    engineer = person "Automation Engineer" "Extends the automation repo, writes tests, and keeps the workflow reproducible."

    automation = softwareSystem "Podcast Automation Platform" "Stage-based Python tooling that replaces the manual production steps." {
      config_store = container "Configuration Files" "TOML defaults under configs/ that ship repeatable stage settings." "TOML files" {
        tags "DataStore"
      }
      sample_assets = container "Sample Assets & Fixtures" "Deterministic audio + template data under assets/ used for tests and demos." "File store" {
        tags "DataStore"
      }
      outputs_workspace = container "Outputs Workspace" "Local scratch space (outputs/) where CLIs drop catalogs, stems, transcripts, and reports." "File store" {
        tags "DataStore"
      }
      transcript_toolkit = container "Transcript Toolkit" "Builds Whisper configs, enforces word replacements, and generates transcripts." "Python 3.11 / automation.transcript"
      common_lib = container "Common Library" "Shared helpers (logging, IO, dataclasses) imported by every stage." "Python / automation.common"
      tests_suite = container "Pytest Suite" "tests/<stage> exercises each CLI with fixtures and mocks." "pytest"
      docs_pack = container "Docs & Playbooks" "Original workflow, plan, TODO, and handoff files that explain operational context." "Markdown"
      ingest_cli = container "Ingest CLI" "Catalogs synced episodes, validates renders, and surfaces recording gaps." "Python 3.11 / automation.ingest.sync"
      edit_cli = container "Edit CLI" "Normalizes tracks, aligns the intro, trims cuts, and exports deterministic stems." "Python 3.11 / automation.edit.cli" {
        edit_cli_runner = component "CLI Runner" "Parses CLI arguments and orchestrates the edit pipeline." "argparse"
        edit_config_builder = component "Config Builder" "Wraps build_edit_config/parse_extensions and merges CLI + TOML settings." "automation.edit.config"
        mix_engine = component "Mix & Alignment" "Combines the host/guest WAVs, enforces intro delay, and tracks wave specs." "automation.edit.mix"
        analysis_engine = component "Sample Analysis" "Computes silence windows, LUFS, and peak metrics." "automation.edit.analysis + automation.edit.meter"
        cut_planner = component "Cut Planner" "Builds silence/noise cut segments and applies them to audio arrays." "automation.edit.cuts"
        transcript_manager = component "Transcript Manager" "Loads/generates transcripts and keeps them aligned with the audio edits." "automation.edit.transcript_sync + automation.transcript"
        guidance_engine = component "AI Guidance" "Summarizes edit heuristics into reviewer prompts." "automation.edit.ai_guidance"
        export_engine = component "Export + Reporting" "Writes mixed audio, stems, edit reports, and cut lists to outputs/." "automation.edit.export"

        edit_cli_runner -> edit_config_builder "Builds effective config from CLI + TOML." "Function call"
        edit_cli_runner -> mix_engine "Creates the mixed master for downstream steps." "Audio buffers"
        edit_cli_runner -> analysis_engine "Requests silence + loudness analysis." "Wave data"
        edit_cli_runner -> cut_planner "Asks for silence/noise cuts to apply." "Cut definitions"
        edit_cli_runner -> transcript_manager "Loads or generates the transcript + intro alignment." "Transcript doc"
        edit_cli_runner -> guidance_engine "Generates reviewer prompts." "Text"
        edit_cli_runner -> export_engine "Writes outputs and reports to disk." "Audio + JSON"
        edit_config_builder -> config_store "Reads edit.toml + overrides." "TOML"
        mix_engine -> analysis_engine "Provides sample arrays to inspect." "Audio samples"
        analysis_engine -> cut_planner "Provides silence/noise windows." "Analysis results"
        cut_planner -> transcript_manager "Shares the final cut list for transcript trimming." "Cut list"
        transcript_manager -> transcript_toolkit "Delegates Whisper generation when no transcript is provided." "Python API"
        transcript_manager -> outputs_workspace "Writes intermediate transcript files." "JSON"
        export_engine -> outputs_workspace "Persists stems, masters, and edit reports." "Audio/JSON"
      }
      export_cli = container "Export Validator" "Future stage that will check LUFS/peak constraints on final renders." "Python / automation.export"
      notes_cli = container "Show Notes CLI" "Summarizes transcripts into publishable episode notes." "Python / automation.notes"
      artwork_cli = container "Artwork CLI" "Generates episode artwork from templates and metadata." "Python / automation.artwork"
      publish_cli = container "Publish CLI" "Pushes episodes to Acast + the Sanity CMS in lockstep." "Python / automation.publish"
    }

    syncthing = softwareSystem "Syncthing Workspace" "Syncs raw host/guest WAVs from the recording Mac Mini." {
      tags "External"
    }
    reaper = softwareSystem "Reaper" "Digital Audio Workstation used for any manual polish." {
      tags "External"
    }
    ffmpeg = softwareSystem "FFmpeg" "Local rendering/encoding utility used by export + edit stages." {
      tags "External"
    }
    whisper_service = softwareSystem "OpenAI Whisper" "Local or API-based speech-to-text model invoked for transcripts." {
      tags "External"
    }
    acast = softwareSystem "Acast" "Podcast hosting provider where episodes are scheduled." {
      tags "External"
    }
    sanity = softwareSystem "Sanity CMS" "Website CMS used to publish Maple History show notes." {
      tags "External"
    }
    archives = softwareSystem "Public Image Archives" "Canadian archives / Wikimedia that feed artwork templates." {
      tags "External"
    }

    producer -> automation "Runs the CLIs, reviews outputs, and feeds decisions back into the workflow."
    engineer -> automation "Adds new stages, updates configs/tests, and keeps automation deterministic."
    automation -> syncthing "Reads synced episode folders and render directories."
    automation -> reaper "Exports stems or pull-ins to assist manual editing when needed."
    automation -> acast "Uploads renders, titles, artwork, and schedules publication."
    automation -> sanity "Creates and syncs CMS entries with Acast IDs." "REST/CLI"
    automation -> archives "Pulls historical imagery + metadata for artwork prompts."
    automation -> whisper_service "Runs Whisper transcription via CLI or local GPU." "Python API"

    producer -> syncthing "Drops recordings from the studio Mac." "Synced folder"
    reaper -> acast "Manual fallback render when automation is skipped." "MP3 upload"
    reaper -> sanity "Provides content for manual CMS edits when automation is bypassed."

    // Container relationships
    producer -> ingest_cli "Runs ingest sync to confirm raw assets." "CLI"
    producer -> edit_cli "Runs edit CLI to generate stems/transcripts." "CLI"
    producer -> notes_cli "Runs show-notes generator." "CLI"
    producer -> artwork_cli "Runs artwork generator." "CLI"
    producer -> publish_cli "Runs publish CLI for CMS/Acast alignment." "CLI"
    engineer -> tests_suite "Runs pytest/ruff before submitting changes." "CLI"
    engineer -> docs_pack "Updates workflow docs as the pipeline evolves."

    ingest_cli -> syncthing "Scans episode folders and render_dir." "File IO"
    ingest_cli -> config_store "Reads ingest.toml overrides." "TOML"
    ingest_cli -> outputs_workspace "Writes ingest reports and stats." "JSON/Text"
    ingest_cli -> docs_pack "Displays workflow warnings defined in docs." "Reference"
    ingest_cli -> common_lib "Uses shared file/path helpers."

    edit_cli -> syncthing "Reads WAV tracks for host/guest/intro." "File IO"
    edit_cli -> sample_assets "Uses fixtures when running tests/demos." "File IO"
    edit_cli -> config_store "Reads edit + transcript configs." "TOML"
    edit_cli -> transcript_toolkit "Requests Whisper transcripts + replacements." "Python API"
    edit_cli -> ffmpeg "Renders WAV/MP3 plus LUFS analysis." "Subprocess"
    edit_cli -> outputs_workspace "Writes stems, mixed masters, and reports." "File IO"
    edit_cli -> common_lib "Uses shared data models/utilities."

    export_cli -> edit_cli "Consumes edited masters for validation." "File IO"
    export_cli -> config_store "Reads export thresholds." "TOML"
    export_cli -> outputs_workspace "Stores validation reports." "JSON"
    export_cli -> common_lib "Shared IO/logging helpers."

    transcript_toolkit -> whisper_service "Loads models, runs transcription jobs." "Python API"
    transcript_toolkit -> config_store "Reads transcript config defaults." "TOML"
    transcript_toolkit -> outputs_workspace "Writes Whisper JSONs." "File IO"
    transcript_toolkit -> common_lib "Shared utilities." "Python"

    notes_cli -> transcript_toolkit "Consumes transcripts for summarization." "Python API"
    notes_cli -> config_store "Reads prompt/formatting rules." "TOML"
    notes_cli -> outputs_workspace "Stores draft notes + metadata." "Markdown"
    notes_cli -> common_lib "Shared logging/IO." "Python"

    artwork_cli -> archives "Fetches historical imagery references." "HTTP/API"
    artwork_cli -> config_store "Reads template + typography config." "TOML"
    artwork_cli -> outputs_workspace "Exports layered + flattened artwork." "PNG/SVG"
    artwork_cli -> common_lib "Shared helpers." "Python"

    publish_cli -> acast "Uploads audio, artwork, and schedule info." "Acast API"
    publish_cli -> sanity "Creates/updates CMS entries with transcript + metadata." "Sanity API"
    publish_cli -> config_store "Reads credential names + schedule policy." "TOML"
    publish_cli -> outputs_workspace "Writes publish logs + receipts." "JSON"
    publish_cli -> common_lib "Shared HTTP + logging helpers." "Python"

    tests_suite -> sample_assets "Uses fixtures for deterministic runs." "File IO"
    tests_suite -> common_lib "Imports shared data models." "Python"
    tests_suite -> ingest_cli "Covers ingest edge cases via unit tests." "Python"
    tests_suite -> edit_cli "Covers edit/trimming logic." "Python"
    tests_suite -> transcript_toolkit "Mocks Whisper interactions." "Python"

    docs_pack -> config_store "Documents expected config keys." "Reference"
  }

  views {
    systemContext automation "context" "System context diagram for the automation platform." {
      include *
      autoLayout lr
    }

    container automation "containers" "Container view outlining each stage + supporting stores." {
      include *
      autoLayout lr
    }

    component edit_cli "edit-components" "Component view for the Edit CLI." {
      include *
      autoLayout lr
    }

    styles {
      element "Person" {
        background "#08427b"
        color "#ffffff"
        shape Person
      }
      element "Software System" {
        background "#1168bd"
        color "#ffffff"
      }
      element "Container" {
        background "#438dd5"
        color "#ffffff"
      }
      element "Component" {
        background "#85bbf0"
        color "#000000"
      }
      element "External" {
        background "#999999"
        color "#ffffff"
      }
      element "DataStore" {
        shape Cylinder
        background "#f5da81"
        color "#000000"
      }
    }
  }
}

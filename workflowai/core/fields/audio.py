"""Audio field for handling audio file inputs."""

from workflowai.core.fields.file import File


class Audio(File):
    """A field representing an audio file.

    This field is used to handle audio inputs in various formats (MP3, WAV, etc.).
    The audio can be provided either as base64-encoded data or as a URL.
    """
    pass

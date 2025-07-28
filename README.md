# Voice Agent - Real-time AI Customer Support

A low-latency voice agent built with Deepgram (STT/TTS), OpenAI (LLM), and LiveKit-inspired pipeline architecture. Designed for sub-second response times in voice conversations.

## Features

- **Ultra-low latency**: Sub-second response times through streaming APIs
- **Real-time processing**: Streaming STT, LLM, and TTS for continuous conversation
- **Pipeline architecture**: Inspired by LiveKit for efficient audio processing
- **Customer support focused**: Optimized prompts and responses for support scenarios
- **Modular design**: Easy to customize and extend

## Architecture

```
Audio Input → STT (Deepgram) → LLM (OpenAI) → TTS (Deepgram) → Audio Output
     ↑                                                              ↓
Microphone ←────────────── Pipeline Controller ──────────────→ Speaker
```

### Components

- **STT Service**: Real-time speech-to-text using Deepgram Nova-2
- **LLM Service**: Streaming chat completion with OpenAI GPT-3.5-turbo  
- **TTS Service**: Text-to-speech synthesis using Deepgram Aura
- **Voice Pipeline**: Orchestrates the entire conversation flow
- **Audio Components**: Microphone and speaker handling with PyAudio

## Installation

### Prerequisites

- Python 3.8+
- Audio device (microphone and speakers)
- Deepgram API key
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd voice-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Test the setup**
   ```bash
   python test_voice_agent.py
   ```

5. **Run the voice agent**
   ```bash
   python main.py
   ```

## Usage

### Quick Start

1. Run the agent: `python main.py`
2. Wait for "🎤 Listening for your voice..." message
3. Speak your question or request
4. Listen to the AI response
5. Continue the conversation naturally

### Configuration

Edit `src/config.py` to customize:

- **Audio settings**: Sample rate, chunk size, channels
- **Model selection**: STT/TTS/LLM model variants
- **Performance tuning**: Timeouts, thresholds, buffer sizes
- **Conversation behavior**: System prompts, response length

### API Keys

#### Deepgram API Key
1. Sign up at [Deepgram](https://console.deepgram.com/)
2. Create a new project
3. Generate an API key
4. Add to `.env` file

#### OpenAI API Key  
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Navigate to API keys section
3. Create a new secret key
4. Add to `.env` file

## Performance Optimization

### Latency Targets
- **STT First Token**: < 200ms
- **LLM First Token**: < 300ms  
- **TTS First Audio**: < 400ms
- **Total Response Time**: < 1000ms

### Optimization Tips

1. **Use streaming everywhere**: All services use streaming APIs
2. **Sentence-level TTS**: Convert complete sentences immediately
3. **Pipeline parallelism**: Process audio while generating response
4. **Efficient audio**: 16kHz sample rate for optimal balance
5. **Local buffering**: Minimize network roundtrips

### Model Selection

**For lowest latency:**
- STT: `nova-2` (Deepgram)
- LLM: `gpt-3.5-turbo` (OpenAI)
- TTS: `aura-asteria-en` (Deepgram)

**For highest quality:**
- STT: `nova-2` (Deepgram)
- LLM: `gpt-4` (OpenAI) 
- TTS: `aura-luna-en` (Deepgram)

## Testing

Run the test suite to verify everything works:

```bash
python test_voice_agent.py
```

Tests include:
- Configuration validation
- API connectivity
- Audio component initialization  
- Service functionality
- End-to-end pipeline simulation
- Latency measurements

## Troubleshooting

### Common Issues

**"No audio device found"**
- Check microphone/speaker connections
- Verify PyAudio installation: `pip install pyaudio`
- On Linux: `sudo apt-get install portaudio19-dev`

**"API key not found"**
- Verify `.env` file exists and contains valid keys
- Check API key format and permissions
- Ensure sufficient API credits

**"Connection failed"**
- Check internet connectivity
- Verify API endpoints are accessible
- Check firewall/proxy settings

**High latency**
- Test network connection speed
- Try different model configurations
- Reduce audio buffer sizes
- Check system CPU usage

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Audio Issues

**Linux audio setup:**
```bash
# Install ALSA development files
sudo apt-get install libasound2-dev

# List audio devices
python -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
```

## Customization

### Custom Prompts

Edit the system prompt in `src/services/llm_service.py`:

```python
def _get_system_prompt(self) -> str:
    return """Your custom system prompt here..."""
```

### Voice Selection

Change TTS voice in `src/config.py`:

```python
DEEPGRAM_TTS_MODEL = "aura-luna-en"  # or other voice models
```

### Audio Parameters

Adjust audio quality vs latency in `src/config.py`:

```python
SAMPLE_RATE = 16000  # Lower = faster, Higher = better quality
CHUNK_SIZE = 1024    # Lower = more responsive, Higher = more stable
```

## Development

### Project Structure

```
voice-agent/
├── src/
│   ├── audio/          # Audio input/output handling
│   ├── services/       # STT, LLM, TTS services  
│   ├── pipeline/       # Main pipeline orchestration
│   └── config.py       # Configuration management
├── main.py            # Application entry point
├── test_voice_agent.py # Test suite
└── requirements.txt   # Dependencies
```

### Adding Features

1. **New TTS provider**: Implement in `src/services/`
2. **Custom audio processing**: Extend `src/audio/`
3. **Pipeline modifications**: Edit `src/pipeline/voice_pipeline.py`
4. **Configuration options**: Add to `src/config.py`

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- Create a GitHub issue
- Check the troubleshooting section
- Review test output for diagnostics
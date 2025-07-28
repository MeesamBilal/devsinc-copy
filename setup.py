#!/usr/bin/env python3
"""
Setup script for Voice Agent
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def check_system_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check operating system
    os_name = platform.system()
    print(f"   Operating System: {os_name}")
    
    if os_name == "Linux":
        # Check for audio libraries on Linux
        try:
            result = subprocess.run(["which", "aplay"], capture_output=True)
            if result.returncode != 0:
                print("⚠️  Audio tools may not be available. Consider installing alsa-utils")
        except:
            pass
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment file"""
    print("🔧 Setting up environment...")
    
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            # Copy example file
            with open(".env.example", "r") as f:
                content = f.read()
            
            with open(".env", "w") as f:
                f.write(content)
                
            print("✅ Created .env file from template")
            print("   Please edit .env with your API keys:")
            print("   - DEEPGRAM_API_KEY")
            print("   - OPENAI_API_KEY")
        else:
            # Create basic .env file
            with open(".env", "w") as f:
                f.write("DEEPGRAM_API_KEY=your_deepgram_api_key_here\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            print("✅ Created basic .env file")
    else:
        print("✅ .env file already exists")
    
    return True

def check_audio_permissions():
    """Check if audio permissions are available"""
    print("🎤 Checking audio permissions...")
    
    try:
        import pyaudio
        
        # Try to create PyAudio instance
        audio = pyaudio.PyAudio()
        
        # Check for input devices
        input_devices = []
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])
        
        if input_devices:
            print(f"✅ Found {len(input_devices)} audio input device(s)")
            print(f"   Primary device: {input_devices[0]}")
        else:
            print("⚠️  No audio input devices found")
            
        audio.terminate()
        return True
        
    except ImportError:
        print("⚠️  PyAudio not installed yet")
        return True
    except Exception as e:
        print(f"⚠️  Audio check failed: {e}")
        print("   This may be due to missing system audio libraries")
        return True

def run_basic_test():
    """Run a basic test to verify installation"""
    print("🧪 Running basic test...")
    
    try:
        # Test imports
        from config import Config
        print("✅ Configuration loading works")
        
        # Check if API keys are set (will be placeholder values initially)
        if Config.DEEPGRAM_API_KEY and Config.OPENAI_API_KEY:
            if "your_" not in Config.DEEPGRAM_API_KEY and "your_" not in Config.OPENAI_API_KEY:
                print("✅ API keys appear to be configured")
            else:
                print("⚠️  API keys need to be configured in .env file")
        else:
            print("⚠️  API keys not found in environment")
            
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*50)
    print("🎉 Setup Complete!")
    print("="*50)
    print("Next steps:")
    print("1. Edit .env file with your API keys:")
    print("   - Get Deepgram API key: https://deepgram.com/")
    print("   - Get OpenAI API key: https://openai.com/")
    print()
    print("2. Test the installation:")
    print("   python test_voice_agent.py")
    print()
    print("3. Run the voice agent:")
    print("   python main.py")
    print()
    print("📚 See README.md for detailed documentation")
    print("="*50)

def main():
    """Main setup function"""
    print("🚀 Voice Agent Setup")
    print("="*30)
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
        
    if not check_system_requirements():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Check audio
    check_audio_permissions()
    
    # Run basic test
    if not run_basic_test():
        print("⚠️  Some tests failed, but installation may still work")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
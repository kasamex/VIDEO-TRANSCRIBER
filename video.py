#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIDEO TRANSCRIBER - VERSÃO AVANÇADA
Sistema plug-and-play com detecção de speakers, múltiplos formatos e gravação ao vivo
Instala automaticamente todas as dependências necessárias
"""
import os
import subprocess
import sys
import tempfile
import json
import urllib.request
import zipfile
import shutil
import re
import platform
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta

class EnhancedVideoTranscriber:
    def __init__(self):
        print("🎙️ Iniciando Video Transcriber Avançado...")
        self.system = platform.system().lower()
        self.setup_folders()
        # Idiomas mantidos para exibição e detecção, mas sem funcionalidade de tradução
        self.languages = {
            'pt': 'Português',
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'ja': '日本語',
            'ko': '한국어',
            'zh': '中文',
            'ru': 'Русский'
        }

    def setup_folders(self):
        """Criar estrutura de pastas"""
        base_dir = Path(__file__).parent
        self.folders = {
            'downloads': base_dir / 'video_downloads',
            'audio': base_dir / 'extracted_audio',
            'transcripts': base_dir / 'transcriptions',
            'tools': base_dir / 'video_tools',
            'models': base_dir / 'translation_models', # Pasta mantida por compatibilidade
            'recordings': base_dir / 'live_recordings'
        }
        for folder_path in self.folders.values():
            folder_path.mkdir(exist_ok=True)
            print(f"✅ {folder_path.name}: {folder_path}")

    def install_package(self, package_name, import_name=None):
        """Instalar pacote Python"""
        if import_name is None:
            import_name = package_name
        try:
            __import__(import_name)
            print(f"✅ {package_name} já instalado")
            return True
        except ImportError:
            print(f"📦 Instalando {package_name}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package_name,
                    '--quiet', '--disable-pip-version-check'
                ])
                print(f"✅ {package_name} instalado com sucesso!")
                return True
            except Exception as e:
                print(f"❌ Erro instalando {package_name}: {e}")
                return False

    def setup_dependencies(self):
        """Instalar todas as dependências automaticamente"""
        print("\n🔧 Configurando dependências...")
        # Lista de dependências essenciais (argostranslate removido)
        dependencies = [
            ('yt-dlp', 'yt_dlp'),
            ('openai-whisper', 'whisper'),
            ('torch', 'torch'),
            ('torchaudio', 'torchaudio'),
            ('pyaudio', 'pyaudio'),
            ('librosa', 'librosa'),
            ('pyannote.audio', 'pyannote'),
            ('reportlab', 'reportlab'),
            ('sounddevice', 'sounddevice'),
            ('scipy', 'scipy'),
            ('numpy', 'numpy'),
        ]
        failed_deps = []
        for package, import_name in dependencies:
            if not self.install_package(package, import_name):
                failed_deps.append(package)
        if failed_deps:
            print(f"⚠️ Falha ao instalar: {', '.join(failed_deps)}")
            print("⚠️ Algumas funcionalidades podem não funcionar")
        print("✅ Setup de dependências concluído!")
        return True

    def setup_ffmpeg(self):
        """Configurar FFmpeg automaticamente - Prioriza o local da pasta tools"""
        # 1. Verificar se já existe na pasta tools PRIMEIRO
        ffmpeg_path = self.folders['tools'] / ('ffmpeg.exe' if self.system == 'windows' else 'ffmpeg')
        if ffmpeg_path.exists():
            print("✅ FFmpeg encontrado na pasta tools")
            # Adicionar ao PATH para que o Whisper encontre
            os.environ['PATH'] = str(self.folders['tools']) + os.pathsep + os.environ.get('PATH', '')
            return str(ffmpeg_path)
        
        # 2. TENTAR FFmpeg do sistema
        try:
            print("🔍 Verificando FFmpeg do sistema...")
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                check=True,
                shell=(self.system == 'windows')
            )
            if result.returncode == 0:
                print("✅ FFmpeg do sistema disponível")
                return 'ffmpeg'
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"⚠️ FFmpeg do sistema não encontrado ou não funcionando: {e}")
        except Exception as e:
             print(f"⚠️ Erro inesperado ao verificar FFmpeg do sistema: {e}")

        # 3. Download automático para Windows
        if self.system == 'windows':
            downloaded_path = self.download_ffmpeg_windows()
            if downloaded_path:
                # Adicionar ao PATH após download
                os.environ['PATH'] = str(self.folders['tools']) + os.pathsep + os.environ.get('PATH', '')
                return downloaded_path
            else:
                print("❌ Falha ao baixar FFmpeg.")

        # 4. Último recurso: Avisar para instalar manualmente
        print("⚠️ FFmpeg não encontrado. É essencial para o funcionamento.")
        print("💡 Tente instalar manualmente:")
        if self.system == 'windows':
            print("   - winget install FFmpeg")
            print("   - Ou baixe de https://www.gyan.dev/ffmpeg/builds/ e adicione ao PATH")
        else:
            print("   - Ubuntu/Debian: sudo apt install ffmpeg")
            print("   - macOS: brew install ffmpeg")
        return None

    def download_ffmpeg_windows(self):
        """Download automático do FFmpeg para Windows"""
        print("📥 Baixando FFmpeg para Windows...")
        try:
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            temp_zip = tempfile.gettempdir() + "/ffmpeg.zip"
            # Download
            urllib.request.urlretrieve(url, temp_zip)
            # Extrair
            temp_dir = tempfile.gettempdir() + "/ffmpeg_temp"
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            # Encontrar e mover executáveis
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file in ['ffmpeg.exe', 'ffprobe.exe']:
                        src = os.path.join(root, file)
                        dst = self.folders['tools'] / file
                        shutil.move(src, dst)
            # Limpeza
            shutil.rmtree(temp_dir, ignore_errors=True)
            os.remove(temp_zip)
            ffmpeg_path = self.folders['tools'] / 'ffmpeg.exe'
            if ffmpeg_path.exists():
                print("✅ FFmpeg baixado e configurado!")
                return str(ffmpeg_path)
        except Exception as e:
            print(f"❌ Erro baixando FFmpeg: {e}")
        return None

    def record_audio_live(self, duration_seconds=None):
        """Gravar áudio ao vivo do microfone"""
        print("🎤 Iniciando gravação ao vivo...")
        try:
            import sounddevice as sd
            import numpy as np
            from scipy.io.wavfile import write
            # Configurações de gravação
            sample_rate = 16000  # Hz
            channels = 1  # Mono
            if duration_seconds:
                print(f"⏱️ Gravando por {duration_seconds} segundos...")
                print("🔴 Gravando... Fale agora!")
                # Gravar por tempo determinado
                audio_data = sd.rec(
                    int(duration_seconds * sample_rate),
                    samplerate=sample_rate,
                    channels=channels,
                    dtype=np.int16
                )
                sd.wait()  # Aguardar conclusão
            else:
                print("🔴 Gravando... Pressione Enter para parar!")
                # Gravar até o usuário pressionar Enter
                audio_chunks = []

                def callback(indata, frames, time, status):
                    audio_chunks.append(indata.copy())

                # Iniciar stream
                stream = sd.InputStream(
                    callback=callback,
                    samplerate=sample_rate,
                    channels=channels,
                    dtype=np.int16
                )
                with stream:
                    input()  # Aguardar Enter
                # Concatenar chunks
                if audio_chunks:
                    audio_data = np.concatenate(audio_chunks, axis=0)
                else:
                    print("❌ Nenhum áudio gravado")
                    return None
            # Salvar arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            filepath = self.folders['recordings'] / filename
            write(str(filepath), sample_rate, audio_data)
            file_size = filepath.stat().st_size / (1024 * 1024)
            duration = len(audio_data) / sample_rate
            print(f"✅ Gravação salva: {filename}")
            print(f"📊 Duração: {duration:.1f}s, Tamanho: {file_size:.1f}MB")
            return str(filepath)
        except ImportError:
            print("❌ Biblioteca de áudio não instalada")
            print("Instale com: pip install sounddevice scipy")
            return None
        except Exception as e:
            print(f"❌ Erro na gravação: {e}")
            return None

    def detect_speakers(self, audio_path):
        """Detectar e separar speakers no áudio"""
        print("👥 Detectando speakers...")
        try:
            from pyannote.audio import Pipeline
            # Carregar pipeline de diarização
            print("📦 Carregando modelo de detecção de speakers...")
            print("⏳ Primeira vez pode demorar (download do modelo)...")
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            # Processar áudio
            print("🔄 Analisando speakers...")
            diarization = pipeline(audio_path)
            # Extrair informações dos speakers
            speakers_info = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speakers_info.append({
                    'speaker': speaker,
                    'start': turn.start,
                    'end': turn.end,
                    'duration': turn.end - turn.start
                })
            # Estatísticas
            unique_speakers = set(info['speaker'] for info in speakers_info)
            print(f"✅ Detectados {len(unique_speakers)} speakers:")
            for speaker in sorted(unique_speakers):
                speaker_time = sum(
                    info['duration'] for info in speakers_info
                    if info['speaker'] == speaker
                )
                print(f"  {speaker}: {speaker_time:.1f}s")
            return speakers_info
        except ImportError:
            print("❌ pyannote.audio não instalado")
            print("Instale com: pip install pyannote.audio")
            return None
        except Exception as e:
            print(f"❌ Erro na detecção de speakers: {e}")
            return None

    def transcribe_with_speakers(self, audio_path):
        """Transcrever áudio com detecção de speakers"""
        print("🎙️ Transcrevendo com detecção de speakers...")
        # Primeira transcrição normal
        transcription_data, language = self.transcribe_audio(audio_path)
        if not transcription_data:
            return None, None
        # Detecção de speakers
        speakers_info = self.detect_speakers(audio_path)
        if speakers_info:
            # Combinar transcrição com speakers
            print("🔗 Combinando transcrição com speakers...")
            # Simplificado: associar segmentos de tempo
            enhanced_transcription = {
                'language': language,
                'text': transcription_data['text'] if isinstance(transcription_data, dict) else transcription_data,
                'segments': transcription_data.get('segments', []) if isinstance(transcription_data, dict) else [],
                'speakers': speakers_info
            }
            return enhanced_transcription, language
        else:
            # Fallback para transcrição normal
            return transcription_data, language

    def export_to_srt(self, transcription_data, output_path):
        """Exportar transcrição para formato SRT (legendas)"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if isinstance(transcription_data, dict) and 'segments' in transcription_data:
                    # Com timestamps
                    for i, segment in enumerate(transcription_data['segments'], 1):
                        start_time = self.seconds_to_srt_time(segment['start'])
                        end_time = self.seconds_to_srt_time(segment['end'])
                        text = segment['text'].strip()
                        f.write(f"{i}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
                else:
                    # Sem timestamps - dividir em blocos
                    text = transcription_data['text'] if isinstance(transcription_data, dict) else transcription_data
                    words = text.split()
                    words_per_subtitle = 10
                    duration_per_subtitle = 3
                    for i in range(0, len(words), words_per_subtitle):
                        chunk = ' '.join(words[i:i+words_per_subtitle])
                        start_seconds = i // words_per_subtitle * duration_per_subtitle
                        end_seconds = start_seconds + duration_per_subtitle
                        start_time = self.seconds_to_srt_time(start_seconds)
                        end_time = self.seconds_to_srt_time(end_seconds)
                        f.write(f"{i//words_per_subtitle + 1}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{chunk}\n\n")
            print(f"✅ SRT salvo: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Erro salvando SRT: {e}")
            return False

    def seconds_to_srt_time(self, seconds):
        """Converter segundos para formato SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def export_to_json(self, transcription_data, output_path):
        """Exportar para JSON com metadados completos"""
        try:
            export_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'tool': 'Enhanced Video Transcriber',
                    'whisper_model': 'base'
                },
                'transcription': transcription_data
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON salvo: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Erro salvando JSON: {e}")
            return False

    def export_to_pdf(self, title, original_text, translated_text, source_lang, target_lang, output_path):
        """Exportar para PDF formatado"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            # Criar documento
            doc = SimpleDocTemplate(str(output_path), pagesize=A4)
            styles = getSampleStyleSheet()
            # Estilos customizados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
            )
            # Conteúdo
            story = []
            # Título
            story.append(Paragraph(f"TRANSCRIÇÃO - {title}", title_style))
            story.append(Spacer(1, 12))
            # Metadados
            story.append(Paragraph("INFORMAÇÕES", heading_style))
            story.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            story.append(Paragraph(f"Idioma original: {self.languages.get(source_lang, source_lang)}", styles['Normal']))
            story.append(Spacer(1, 20))
            # Transcrição original
            story.append(Paragraph("TRANSCRIÇÃO ORIGINAL", heading_style))
            # Quebrar texto em parágrafos
            paragraphs = original_text.split('\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), styles['Normal']))
                    story.append(Spacer(1, 6))
            # Gerar PDF
            doc.build(story)
            print(f"✅ PDF salvo: {output_path}")
            return True
        except ImportError:
            print("❌ reportlab não instalado")
            print("Instale com: pip install reportlab")
            return False
        except Exception as e:
            print(f"❌ Erro salvando PDF: {e}")
            return False

    def download_video(self, url):
        """Download de vídeo do YouTube"""
        try:
            import yt_dlp
            output_template = str(self.folders['downloads'] / '%(title)s.%(ext)s')
            ydl_opts = {
                'format': 'best[height<=720]/best',
                'outtmpl': output_template,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("🔍 Obtendo informações do vídeo...")
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'video')
                duration = info.get('duration', 0)
                print(f"📹 Título: {title}")
                if duration:
                    print(f"⏱️ Duração: {duration//60}:{duration%60:02d}")
                if duration > 3600:  # > 1 hora
                    response = input("\n⚠️ Vídeo longo (>1h). Continuar? (s/n): ")
                    if response.lower() not in ['s', 'sim', 'y', 'yes']:
                        return None, None
                print("\n📥 Baixando vídeo...")
                ydl.download([url])
                # Encontrar arquivo baixado
                for file_path in self.folders['downloads'].glob('*'):
                    if file_path.suffix.lower() in ['.mp4', '.mkv', '.avi', '.mov', '.webm']:
                        print(f"✅ Baixado: {file_path.name}")
                        return str(file_path), title
        except Exception as e:
            print(f"❌ Erro no download: {e}")
        return None, None

    def extract_audio(self, video_path, title, ffmpeg_cmd):
        """Extrair áudio do vídeo"""
        print("🎵 Extraindo áudio...")
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        audio_path = self.folders['audio'] / f"{safe_title}.wav"
        cmd = [
            ffmpeg_cmd,
            '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            '-loglevel', 'error',
            str(audio_path), '-y'
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            if audio_path.exists():
                size_mb = audio_path.stat().st_size / (1024 * 1024)
                print(f"✅ Áudio extraído: {audio_path.name} ({size_mb:.1f}MB)")
                return str(audio_path)
        except Exception as e:
            print(f"❌ Erro extraindo áudio: {e}")
        return None

    def transcribe_audio(self, audio_path):
        """Transcrever áudio com Whisper - VERSÃO CORRIGIDA"""
        print("🎙️ Transcrevendo áudio...")
        print("⏳ Primeira vez pode demorar (download do modelo)...")
        
        # CORREÇÃO CRÍTICA: Configurar FFmpeg ANTES de importar whisper
        import os
        import sys
        from pathlib import Path
        
        # Adicionar a pasta video_tools ao PATH
        ffmpeg_dir = str(self.folders['tools'])
        if os.path.exists(ffmpeg_dir):
            # Adicionar ao início do PATH (maior prioridade)
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            print(f"📁 Usando FFmpeg de: {ffmpeg_dir}")
        
        try:
            # IMPORTANTE: Importar whisper DEPOIS de configurar o PATH
            import whisper
            
            print("📦 Carregando modelo Whisper...")
            model = whisper.load_model("base")
            
            print("🔄 Transcrevendo...")
            # Converter Path para string se necessário
            audio_path_str = str(audio_path) if not isinstance(audio_path, str) else audio_path
            
            # Verificar se o arquivo de áudio existe
            if not os.path.exists(audio_path_str):
                print(f"❌ Arquivo de áudio não encontrado: {audio_path_str}")
                return None, None
            
            result = model.transcribe(audio_path_str, verbose=False)
            
            text = result.get('text', '').strip()
            language = result.get('language', 'unknown')
            
            if text:
                print(f"✅ Transcrição concluída! ({len(text)} caracteres)")
                print(f"🌍 Idioma detectado: {self.languages.get(language, language)}")
                return result, language
            else:
                print("⚠️ Nenhum texto foi transcrito (arquivo pode estar silencioso ou corrompido)")
                return None, None
                
        except ImportError as e:
            print(f"❌ Erro importando Whisper: {e}")
            print("Execute: pip install openai-whisper")
            return None, None
        except FileNotFoundError as e:
            print(f"❌ FFmpeg não encontrado pelo Whisper")
            print(f"Detalhes: {e}")
            return None, None
        except Exception as e:
            print(f"❌ Erro na transcrição: {e}")
            # Imprimir mais detalhes para debug
            import traceback
            print("Detalhes do erro:")
            traceback.print_exc()
            return None, None

    def translate_text(self, text, target_lang, source_lang):
        """Função de tradução desativada - retorna o texto original"""
        # Tradução offline removida
        print("ℹ️ Função de tradução automática offline foi removida.")
        return text

    def save_all_formats(self, title, transcription_data, translated_text, source_lang, target_lang):
        """Salvar em todos os formatos disponíveis"""
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        base_path = self.folders['transcripts'] / safe_title
        # Texto da transcrição
        original_text = transcription_data['text'] if isinstance(transcription_data, dict) else transcription_data
        results = {}
        # 1. TXT tradicional
        txt_path = f"{base_path}_transcription.txt"
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"TRANSCRIÇÃO - {title}\n")
                f.write("=" * 60 + "\n")
                f.write(f"TRANSCRIÇÃO ORIGINAL ({self.languages.get(source_lang, source_lang)}):\n")
                f.write("-" * 40 + "\n")
                f.write(original_text + "\n")
                f.write("\nGerado por Enhanced Video Transcriber\n")
            results['txt'] = txt_path
            print(f"✅ TXT salvo: {Path(txt_path).name}")
        except Exception as e:
            print(f"❌ Erro salvando TXT: {e}")
        # 2. JSON
        json_path = f"{base_path}_data.json"
        if self.export_to_json(transcription_data, json_path):
            results['json'] = json_path
        # 3. SRT
        srt_path = f"{base_path}_subtitles.srt"
        if self.export_to_srt(transcription_data, srt_path):
            results['srt'] = srt_path
        # 4. PDF
        pdf_path = f"{base_path}_document.pdf"
        # Passa o mesmo texto para original e traduzido para evitar bloco de tradução no PDF
        if self.export_to_pdf(title, original_text, original_text, source_lang, target_lang, pdf_path):
            results['pdf'] = pdf_path
        return results

    def process_audio_file(self, audio_path, title, target_lang='pt', detect_speakers=False):
        """Processar arquivo de áudio direto"""
        print(f"🔊 Processando arquivo de áudio: {title}")
        try:
            # Escolher método de transcrição
            if detect_speakers:
                transcription_data, source_lang = self.transcribe_with_speakers(audio_path)
            else:
                transcription_data, source_lang = self.transcribe_audio(audio_path)
            if not transcription_data:
                return False
            # Extrair texto principal
            original_text = transcription_data['text'] if isinstance(transcription_data, dict) else transcription_data
            # Mostrar transcrição
            print("\n" + "="*60)
            print("TRANSCRIÇÃO:")
            print("="*60)
            preview = original_text[:300] + ("..." if len(original_text) > 300 else "")
            print(preview)
            print()
            # Tradução removida - não perguntar mais
            translated_text = original_text # Sempre usar o texto original
            print("✅ Salvando transcrição")

            # Salvar em todos os formatos
            saved_files = self.save_all_formats(
                title, transcription_data, translated_text,
                source_lang, target_lang
            )
            print(f"\n📁 Arquivos salvos: {len(saved_files)}")
            for format_type, file_path in saved_files.items():
                print(f"  {format_type.upper()}: {Path(file_path).name}")
            return len(saved_files) > 0
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            return False

    def process_video(self, video_source, target_lang='pt', detect_speakers=False):
        """Processar vídeo (URL ou arquivo local)"""
        title = None
        video_path = None
        # Determinar se é URL ou arquivo
        if video_source.startswith(('http://', 'https://', 'www.')):
            video_path, title = self.download_video(video_source)
            if not video_path:
                return False
        else:
            video_path = video_source
            if not os.path.exists(video_path):
                print("❌ Arquivo não encontrado!")
                return False
            title = Path(video_path).stem
        # Obter comando FFmpeg
        ffmpeg_cmd = self.setup_ffmpeg()
        if not ffmpeg_cmd:
            print("❌ FFmpeg necessário!")
            return False
        # Extrair áudio
        audio_path = self.extract_audio(video_path, title, ffmpeg_cmd)
        if not audio_path:
            return False
        try:
            # Processar áudio
            result = self.process_audio_file(audio_path, title, target_lang, detect_speakers)
            return result
        finally:
            # Limpeza
            try:
                os.remove(audio_path)
            except:
                pass

    def live_recording_session(self, target_lang='pt', detect_speakers=False):
        """Sessão de gravação ao vivo"""
        print("\n🎤 === GRAVAÇÃO AO VIVO ===")
        print("Escolha o modo de gravação:")
        print("1. ⏱️ Tempo determinado")
        print("2. 🔴 Pressionar Enter para parar")
        choice = input("Modo (1 ou 2): ").strip()
        duration = None
        if choice == '1':
            try:
                duration = int(input("Duração em segundos: "))
            except ValueError:
                print("❌ Duração inválida, usando modo manual")
                duration = None
        # Gravar
        audio_path = self.record_audio_live(duration)
        if not audio_path:
            return False
        # Processar gravação
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = f"Gravação_{timestamp}"
        result = self.process_audio_file(audio_path, title, target_lang, detect_speakers)
        # Opção de manter arquivo de áudio
        keep_audio = input("\n💾 Manter arquivo de áudio original? (s/n): ").strip().lower()
        if keep_audio not in ['s', 'sim', 'y', 'yes']:
            try:
                os.remove(audio_path)
                print("🗑️ Arquivo de áudio removido")
            except:
                pass
        return result

    def run(self):
        """Menu principal"""
        print("=" * 70)
        print("      VIDEO TRANSCRIBER - VERSÃO AVANÇADA")
        print("  Transcrição + Detecção de Speakers + Múltiplos Formatos")
        print("=" * 70)
        # Setup automático
        print("\n🚀 Configuração automática...")
        if not self.setup_dependencies():
            print("❌ Falha na configuração!")
            return
        # setup_translation_models REMOVIDO
        print("\n✅ Sistema avançado pronto!")
        # Menu principal
        target_language = 'pt' # Mantido para compatibilidade e detecção de idioma
        while True:
            print("\n" + "="*60)
            print("MENU PRINCIPAL - VERSÃO AVANÇADA")
            print("="*60)
            print("1. 📺 Transcrever vídeo do YouTube")
            print("2. 📁 Transcrever arquivo de vídeo local")
            print("3. 🔊 Transcrever arquivo de áudio (MP3/WAV)")
            print("4. 🎤 Gravação ao vivo do microfone")
            print("5. 🌍 (Desativado) Escolher idioma de tradução")
            print("6. 👥 Ativar/desativar detecção de speakers")
            print("7. 📂 Abrir pasta de resultados")
            print("8. ℹ️  Sobre funcionalidades avançadas")
            print("9. 🚪 Sair")
            print(f"\n🌐 Idioma de transcrição detectado: {self.languages.get(target_language, target_language)}")
            # Status da detecção de speakers
            speakers_enabled = getattr(self, 'speakers_enabled', False)
            print(f"👥 Detecção de speakers: {'✅ Ativada' if speakers_enabled else '❌ Desativada'}")
            print("📝 Formatos de saída: TXT, JSON, SRT, PDF")
            try:
                choice = input("\nEscolha: ").strip()
                if choice == '1':
                    url = input("\n🔗 URL do YouTube: ").strip()
                    if url:
                        success = self.process_video(url, target_language, speakers_enabled)
                        print("\n🎉 Concluído!" if success else "\n❌ Erro no processo")
                elif choice == '2':
                    file_path = input("\n📁 Caminho do arquivo de vídeo: ").strip().replace('"', '')
                    if file_path:
                        success = self.process_video(file_path, target_language, speakers_enabled)
                        print("\n🎉 Concluído!" if success else "\n❌ Erro no processo")
                elif choice == '3':
                    file_path = input("\n🔊 Caminho do arquivo de áudio: ").strip().replace('"', '')
                    if file_path and os.path.exists(file_path):
                        title = Path(file_path).stem
                        success = self.process_audio_file(file_path, title, target_language, speakers_enabled)
                        print("\n🎉 Concluído!" if success else "\n❌ Erro no processo")
                    elif file_path:
                        print("❌ Arquivo não encontrado!")
                elif choice == '4':
                    success = self.live_recording_session(target_language, speakers_enabled)
                    print("\n🎉 Gravação processada!" if success else "\n❌ Erro na gravação")
                elif choice == '5':
                    # Opção desativada
                    print("\nℹ️ A funcionalidade de tradução automática offline foi removida.")
                    print("💡 Você pode copiar o texto transcrito e usar um serviço online como Google Tradutor.")
                elif choice == '6':
                    speakers_enabled = not getattr(self, 'speakers_enabled', False)
                    self.speakers_enabled = speakers_enabled
                    status = "ativada" if speakers_enabled else "desativada"
                    print(f"👥 Detecção de speakers {status}")
                    if speakers_enabled:
                        print("ℹ️  Isso detectará diferentes falantes no áudio")
                        print("⏳ Primeira vez pode demorar (download do modelo)")
                elif choice == '7':
                    try:
                        if self.system == 'windows':
                            os.startfile(self.folders['transcripts'])
                        else:
                            subprocess.run(['xdg-open', str(self.folders['transcripts'])])
                        print("📂 Pasta aberta!")
                    except:
                        print(f"📂 Pasta: {self.folders['transcripts']}")
                elif choice == '8':
                    print("\n" + "="*60)
                    print("FUNCIONALIDADES AVANÇADAS")
                    print("="*60)
                    print("\n🎙️ TRANSCRIÇÃO APRIMORADA:")
                    print("  ✅ Whisper (OpenAI) - Estado da arte")
                    print("  ✅ Detecção automática de idioma")
                    print("  ✅ Timestamps precisos para legendas")
                    print("  ✅ Suporte a 99+ idiomas")
                    print("\n👥 DETECÇÃO DE SPEAKERS:")
                    print("  ✅ Identifica diferentes falantes")
                    print("  ✅ Timestamps por speaker")
                    print("  ✅ Estatísticas de tempo de fala")
                    print("  ⏳ Requer modelo adicional (pyannote)")
                    print("\n📁 FORMATOS DE SAÍDA:")
                    print("  📝 TXT - Texto simples formatado")
                    print("  📊 JSON - Dados completos com metadados")
                    print("  🎬 SRT - Legendas para vídeos")
                    print("  📄 PDF - Documento profissional")
                    print("\n🔊 FONTES DE ÁUDIO:")
                    print("  📺 YouTube (yt-dlp)")
                    print("  📁 Arquivos de vídeo locais")
                    print("  🔊 Arquivos de áudio (MP3, WAV, etc.)")
                    print("  🎤 Gravação ao vivo do microfone")
                    print("\n🌐 TRADUÇÃO:")
                    print("  ❌ Tradução automática offline foi removida.")
                    print("  💡 Use a transcrição e um serviço online manualmente.")
                elif choice == '9':
                    print("\n👋 Obrigado por usar o Video Transcriber Avançado!")
                    break
                else:
                    print("\n❌ Opção inválida!")
            except KeyboardInterrupt:
                print("\n👋 Saindo...")
                break
            except Exception as e:
                print(f"\n❌ Erro: {e}")

def main():
    """Função principal"""
    try:
        app = EnhancedVideoTranscriber()
        app.run()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPressione Enter para fechar...")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Teste de configuração do FFmpeg para o Video Transcriber
"""
import os
import subprocess
import sys
from pathlib import Path

def test_ffmpeg():
    print("="*60)
    print("TESTE DE CONFIGURAÇÃO DO FFMPEG")
    print("="*60)
    
    # 1. Verificar pasta video_tools
    script_dir = Path(__file__).parent
    video_tools = script_dir / 'video_tools'
    
    print(f"\n1. Verificando pasta video_tools:")
    print(f"   Caminho: {video_tools}")
    print(f"   Existe: {video_tools.exists()}")
    
    if video_tools.exists():
        ffmpeg_exe = video_tools / 'ffmpeg.exe'
        ffprobe_exe = video_tools / 'ffprobe.exe'
        
        print(f"\n2. Verificando executáveis:")
        print(f"   ffmpeg.exe: {ffmpeg_exe.exists()}")
        print(f"   ffprobe.exe: {ffprobe_exe.exists()}")
        
        if ffmpeg_exe.exists():
            # Adicionar ao PATH
            os.environ['PATH'] = str(video_tools) + os.pathsep + os.environ.get('PATH', '')
            
            print(f"\n3. Testando execução do FFmpeg local:")
            try:
                result = subprocess.run(
                    [str(ffmpeg_exe), '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    print(f"   ✅ FFmpeg funcionando: {version_line}")
                else:
                    print(f"   ❌ FFmpeg retornou erro: {result.stderr}")
            except Exception as e:
                print(f"   ❌ Erro executando FFmpeg: {e}")
    
    # 2. Testar FFmpeg do sistema
    print(f"\n4. Testando FFmpeg do sistema (PATH):")
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            shell=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"   ✅ FFmpeg encontrado no PATH do sistema")
        else:
            print(f"   ❌ FFmpeg não encontrado no PATH")
    except Exception as e:
        print(f"   ❌ FFmpeg não acessível: {e}")
    
    # 3. Testar importação do whisper
    print(f"\n5. Testando biblioteca Whisper:")
    try:
        import whisper
        print(f"   ✅ Whisper importado com sucesso")
        
        # Verificar se whisper consegue encontrar ffmpeg
        import whisper.audio
        print(f"   ℹ️ Whisper audio módulo carregado")
        
    except ImportError as e:
        print(f"   ❌ Whisper não instalado: {e}")
        print(f"   Execute: pip install openai-whisper")
    except Exception as e:
        print(f"   ❌ Erro com Whisper: {e}")
    
    # 4. Teste completo com arquivo de áudio pequeno
    print(f"\n6. Teste de transcrição (se possível):")
    
    # Criar um arquivo de teste silencioso
    test_audio = script_dir / 'test_audio.wav'
    
    try:
        if ffmpeg_exe.exists():
            # Criar arquivo de áudio de teste (1 segundo de silêncio)
            cmd = [
                str(ffmpeg_exe),
                '-f', 'lavfi',
                '-i', 'anullsrc=duration=1',
                '-ar', '16000',
                str(test_audio),
                '-y'
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
            
            if test_audio.exists():
                print(f"   ✅ Arquivo de teste criado")
                
                # Tentar transcrever
                try:
                    import whisper
                    model = whisper.load_model("base")
                    result = model.transcribe(str(test_audio))
                    print(f"   ✅ Transcrição bem-sucedida (teste de silêncio)")
                    
                except Exception as e:
                    print(f"   ❌ Erro na transcrição de teste: {e}")
                
                # Limpar arquivo de teste
                test_audio.unlink()
            else:
                print(f"   ⚠️ Não foi possível criar arquivo de teste")
    except Exception as e:
        print(f"   ⚠️ Teste de transcrição não executado: {e}")
    
    print("\n" + "="*60)
    print("RESULTADO DO DIAGNÓSTICO:")
    print("="*60)
    
    if video_tools.exists() and (video_tools / 'ffmpeg.exe').exists():
        print("\n✅ FFmpeg está presente na pasta video_tools")
        print("💡 Se o script principal não funcionar, substitua a função")
        print("   transcribe_audio() pela versão corrigida fornecida.")
    else:
        print("\n❌ FFmpeg não encontrado na pasta esperada")
        print("💡 Verifique se os arquivos estão na pasta correta")
    
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    test_ffmpeg()
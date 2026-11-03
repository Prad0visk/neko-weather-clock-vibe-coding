# Guia para IAs e contribuidores

Este documento fornece o contexto do projeto sem depender do histórico privado de uma conversa. Leia-o antes de sugerir ou fazer alterações. A fonte completa, com a estrutura original de diretórios, está em `Neko_Weather_Clock_Source.zip`.

## Objetivo e escopo

O projeto cria um tema visual em português brasileiro para relógios GeekMagic/SmallTV com tela 240 × 240 e firmware SmallTV Mod compatível. O dispositivo confirmado pelo responsável é um ESP8266EX. O resultado distribuível é `Neko_Clima_BR_Demo.stheme`; isso é um pacote de tema, não firmware.

O tema apresenta hora e data, cidade, temperatura, umidade relativa, condição do tempo e sensação térmica. A cena inclui Neko piscando, chuva limitada às janelas e atrás das lanternas, e variação sutil da luz. O firmware tem limite de 32 camadas; o tema atual usa 31. Preserve o alinhamento do gato e da almofada durante o piscar.

## Estrutura da fonte

- `scripts/build_theme.py`: constrói os elementos da cena, quadros de animação, prévias e pacote `.stheme`.
- `tools/sti_codec.py`: codifica imagens para o formato STI usado pelo empacotador.
- `assets/`: arte de origem, incluindo a folha de sprites do Neko e o cenário vazio.
- `.build/`: arquivos intermediários gerados pelo construtor; recrie-os, não os trate como fonte principal.
- `dist/`: tema final gerado.
- `docs/images/`: prévias estáticas e animadas.
- `config.example.json`: localização pública genérica de demonstração (Brasília/DF).
- `config.local.json`: configuração local opcional, ignorada pelo Git; nunca publique coordenadas privadas.

Os arquivos `build_theme.py` e `sti_codec.py` na raiz deste repositório são cópias navegáveis para leitura direta no GitHub. Para compilar, use o ZIP completo e a estrutura `scripts/` e `tools/` descrita acima.

## Preparar e reproduzir

Requer Python 3.10 ou superior e acesso à internet apenas para instalar Pillow, caso ainda não esteja instalado. No diretório extraído do ZIP:

```text
python -m pip install -r requirements.txt
python scripts/build_theme.py
```

O construtor lê `config.local.json` quando presente; caso contrário, usa `config.example.json`. Ele gera `dist/Neko_Clima_BR_Demo.stheme` e prévias em `docs/images/`. O script gera arte e arquivo de tema localmente. Ele não se conecta ao relógio, não procura dispositivos na rede e não grava firmware.

Para testar outra localização, copie `config.example.json` para `config.local.json` e ajuste `city_label`, `latitude`, `longitude` e `timezone`. Use um rótulo curto (até 20 caracteres), latitude entre -90 e 90, longitude entre -180 e 180 e fuso IANA, por exemplo `America/Sao_Paulo`. Não inclua essa configuração local em commits ou capturas públicas.

## Orientações para alterações

1. Preserve 240 × 240 pixels, o limite de 32 camadas e a compatibilidade com SmallTV Mod/ESP8266.
2. Mantenha os dados de demonstração genéricos e nunca acrescente IP, MAC, SSID, número de série, credenciais ou coordenadas residenciais.
3. Não adicione código de rede, descoberta de dispositivos, acesso remoto, telemetria ou gravação de firmware ao construtor.
4. Mantenha a chuva dentro da área das janelas e atrás das lanternas; não mova o Neko nem a almofada ao piscar.
5. Preserve os avisos de licença. Consulte `LICENSE`, `ASSET_LICENSES.md` e `THIRD_PARTY_NOTICES.md` antes de reutilizar ou substituir arte/código.
6. Após mudanças no construtor, rode os dois comandos de reprodução acima e confira o tema e as prévias geradas. Não afirme que o relógio físico foi testado sem teste real no dispositivo.
7. Explique no resumo o que mudou, como reproduzir e quais verificações foram feitas. Não invente proveniência, resultados ou compatibilidade.

## Limitações conhecidas

- Os valores exibidos na imagem de apresentação são ilustrativos, não medições ao vivo.
- O repositório contém tema e ferramentas de geração; não contém firmware personalizado.
- A aparência e a atualização meteorológica no relógio dependem do firmware, da configuração do próprio relógio, da rede e do serviço meteorológico usados pelo dispositivo.
- A imagem de referência original tem restrição de reutilização indicada nos avisos de licença.

## Contexto de publicação

Este é um portfólio de Vibe Coding assistido por IA e dirigido por uma pessoa. O objetivo é tornar o processo e o artefato analisáveis e reproduzíveis. O histórico pessoal do chat não é necessário nem deve ser copiado para o repositório.

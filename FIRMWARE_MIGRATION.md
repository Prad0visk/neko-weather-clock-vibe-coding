# Firmware original → SmallTV Mod → tema Neko

Este guia explica a etapa que vem antes de instalar o tema. O tema Neko foi criado para o mecanismo de temas do **SmallTV Mod**; ele não roda diretamente no firmware original GeekMagic e não é um firmware independente.

## O que cada parte faz

1. **Firmware original GeekMagic:** software que veio no relógio. No caso documentado neste portfólio, foi substituído pelo SmallTV Mod.
2. **SmallTV Mod:** firmware de terceiros que substitui o firmware original e fornece, entre outros recursos, a interface web e o suporte a temas.
3. **Tema Neko (`.stheme`):** pacote de dados, imagens e animações instalado dentro do SmallTV Mod. Não contém código executável nem grava firmware.

O código e os binários do SmallTV Mod pertencem ao projeto upstream. Este repositório não os modifica, compila, distribui nem incorpora. Consulte a [documentação oficial](https://giovi321.github.io/smalltv-mod/) e as [versões oficiais](https://github.com/giovi321/smalltv-mod/releases) para instruções atuais e arquivos correspondentes ao seu aparelho.

## Identifique a placa antes de atualizar

A mesma carcaça de relógio pode conter placas diferentes. O projeto SmallTV Mod lista variantes ESP8266, ESP32-C2/ESP8684, ESP32 e SmallTV Pro, com arquivos e procedimentos de instalação distintos. Um adaptador USB-Serial CH340, isoladamente, não identifica a placa do relógio.

No histórico deste projeto, o chip foi consultado pela porta serial e o resultado informado foi **ESP8266EX**. Isso é uma observação daquele aparelho, não uma garantia para outras unidades. Confirme o modelo e siga a [tabela oficial de hardware](https://giovi321.github.io/smalltv-mod/getting-started/hardware/) e o [guia oficial de instalação](https://giovi321.github.io/smalltv-mod/getting-started/flashing/) antes de escolher qualquer arquivo.

Não use um binário apenas porque o nome parece parecido. Por exemplo, a imagem `smalltv-mod-firmware.bin` é descrita pelo upstream para o SmallTV ESP8266 comum, enquanto variantes C2, Pro, Ultra e outras têm distinções próprias. A imagem `lean` exclui o mecanismo de temas no alvo ESP8266 e, portanto, não atende a este tema. Confirme as instruções e a versão atuais na documentação upstream; ela pode mudar.

Uma substituição de firmware remove o software original que estava em execução. Antes de prosseguir, preserve uma cópia do firmware original da **própria unidade** se quiser poder voltar atrás. O SmallTV Mod recomenda fazer esse backup antes da primeira gravação; para o SmallTV ESP8266 comum, o guia oficial descreve a leitura pela UART e informa que o firmware original não é redistribuído pelo upstream. Consulte a seção específica para a sua placa em [Flashing](https://giovi321.github.io/smalltv-mod/getting-started/flashing/) e [Recovery and credits](https://giovi321.github.io/smalltv-mod/reference/recovery/).

## Rollback para o firmware original

Este portfólio **não inclui** um arquivo GeekMagic original genérico. Uma imagem de outra unidade pode não corresponder à placa, à variante ou ao estado de fábrica do seu relógio; além disso, não temos autorização comprovada para redistribuir o binário proprietário. O caminho documentado é guardar `stock-backup.bin` da sua própria unidade antes de instalar SmallTV Mod.

Se quiser retornar ao firmware original:

1. Localize o backup feito antes da troca e confirme que ele pertence à mesma unidade e modelo. Não use um arquivo baixado de um terceiro como substituto.
2. Siga o procedimento UART da seção da sua placa no [guia oficial de instalação e recuperação](https://giovi321.github.io/smalltv-mod/getting-started/flashing/). O procedimento do ESP8266 exige acesso ao cabeçalho UART; a página informa o adaptador de 3,3 V e os pinos necessários.
3. Use a opção de gravação descrita pelo guia para escrever o backup na placa. Essa operação substitui o firmware em execução; confirme placa, porta serial e arquivo antes de executá-la.
4. Se você não criou um backup antes da migração, não presuma que o firmware original possa ser recuperado por OTA ou por uma imagem pública. Consulte o suporte GeekMagic ou o vendedor para uma imagem oficial correspondente ao modelo exato; sem essa imagem ou backup, o rollback pode não ser possível.

Um reset de fábrica do SmallTV Mod apaga configurações e reinicia o modo de configuração, mas **não** restaura o firmware GeekMagic. Firmware de rollback e tema Neko são arquivos e operações separados.

## Sequência depois de confirmar o modelo

Use o procedimento oficial vigente para instalar SmallTV Mod no modelo exato. Na primeira configuração, o firmware pode oferecer a rede temporária `SmallTV-Setup`; siga o [guia oficial de configuração inicial](https://giovi321.github.io/smalltv-mod/getting-started/first-time-setup/) para conectar o relógio ao Wi-Fi e abrir sua interface. Endereço, nomes de menu e fluxo podem variar conforme a versão.

Depois que SmallTV Mod estiver funcionando:

1. Abra a interface web do relógio.
2. Acesse **Display → Theme clocks**.
3. Escolha `Neko_Clima_BR_Demo.stheme`, instale o pacote e selecione **Use theme**.
4. Configure o fuso horário do relógio nas configurações de relógio.

Consulte a [documentação oficial de temas](https://giovi321.github.io/smalltv-mod/features/themes/) para os nomes atuais dos controles e limitações. Atualizar o firmware e instalar/atualizar um tema são operações separadas. Atualizações futuras do firmware são feitas conforme a seção **System** e o manual da versão upstream; o `.stheme` não deve ser enviado como firmware.

## Escopo e privacidade

Este repositório documenta a experiência e distribui somente o tema e seu código-fonte. Não contém IP privado, endereço MAC, SSID, senha, número de série, coordenadas residenciais nem firmware executável. Use o IP local exibido pelo seu próprio relógio; não o publique em capturas ou arquivos de configuração.


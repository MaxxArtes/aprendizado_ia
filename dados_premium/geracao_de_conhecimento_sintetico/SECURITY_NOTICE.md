# Aviso de segurança das fontes excluídas

Na inspeção local de 2026-09-04, uma nota em `../notas_pessoais` continha um token
aparentemente operacional em texto claro,
além de domínios e detalhes de infraestrutura identificáveis. Todo o diretório foi excluído
da geração por lista positiva; nenhum valor sensível foi copiado para os datasets.

Trate o segredo como comprometido e revogue ou rotacione a credencial no provedor. Se a nota
foi enviada a um remoto, remover apenas a linha atual não elimina o valor do histórico Git.
O saneamento do histórico deve ser uma ação separada e consciente.

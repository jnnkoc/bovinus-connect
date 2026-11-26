"""Gerencia os usuários da equipe (login das telas /terminal, /cardapio e /dashboard).

Uso:
  py usuarios.py listar
  py usuarios.py criar <login> <gerente|atendente> "<Nome>"
  py usuarios.py senha <login>
  py usuarios.py desativar <login>
  py usuarios.py ativar <login>

Papéis: gerente = dashboard, cardápio e terminal · atendente = só terminal.
A senha é pedida sem aparecer na tela.
"""
import getpass
import sys
from contextlib import closing

import app


def pedir_senha():
    senha = getpass.getpass("Nova senha (mín. 8 caracteres): ")
    if senha != getpass.getpass("Repita a senha: "):
        sys.exit("As senhas não conferem.")
    return senha


def main(argumentos):
    sys.stdout.reconfigure(encoding="utf-8")
    if not argumentos or argumentos[0] not in ("listar", "criar", "senha", "desativar", "ativar"):
        sys.exit(__doc__)
    app.preparar_banco(criar_usuarios=False)
    comando = argumentos[0]
    with closing(app.conectar()) as banco, banco:
        try:
            if comando == "listar":
                for u in banco.execute("SELECT login, nome, papel, ativo FROM usuario ORDER BY papel, login"):
                    print(f"{u['login']:<15} {u['papel']:<10} {'ativo' if u['ativo'] else 'DESATIVADO':<11} {u['nome']}")
                return
            if len(argumentos) < 2:
                sys.exit(__doc__)
            login = argumentos[1]
            if comando == "criar":
                if len(argumentos) != 4:
                    sys.exit(__doc__)
                app.criar_usuario(banco, login, argumentos[3], argumentos[2], pedir_senha())
                print(f"Usuário {login} criado.")
                return
            existe = banco.execute("SELECT id FROM usuario WHERE login = ?", (login,)).fetchone()
            if not existe:
                sys.exit(f"Usuário {login} não encontrado.")
            if comando == "senha":
                senha = pedir_senha()
                app.validar_senha(senha)
                banco.execute("UPDATE usuario SET senha_hash = ? WHERE id = ?", (app.hash_senha(senha), existe["id"]))
                banco.execute("DELETE FROM sessao WHERE usuario_id = ?", (existe["id"],))
                print(f"Senha de {login} alterada. Sessões abertas foram encerradas.")
            else:
                ativo = int(comando == "ativar")
                banco.execute("UPDATE usuario SET ativo = ? WHERE id = ?", (ativo, existe["id"]))
                if not ativo:
                    banco.execute("DELETE FROM sessao WHERE usuario_id = ?", (existe["id"],))
                print(f"Usuário {login} {'ativado' if ativo else 'desativado'}.")
        except app.ErroAPI as erro:
            sys.exit(str(erro))
        except app.sqlite3.IntegrityError:
            sys.exit(f"Já existe um usuário com o login {login}.")


if __name__ == "__main__":
    main(sys.argv[1:])

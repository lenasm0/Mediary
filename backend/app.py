import psycopg2
import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from functools import wraps
from datetime import datetime, date, timedelta
from psycopg2.extras import RealDictCursor
from flask import (
    request, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "mediary-dev-secret-change-in-prod"),
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
)

# Origens permitidas: FRONTEND_URL + localhost para dev local
_frontend_url = os.environ.get("FRONTEND_URL", "")
_allowed_origins = [o.strip() for o in _frontend_url.split(",") if o.strip()]
_allowed_origins += ["http://localhost", "http://localhost:80", "http://127.0.0.1"]

CORS(
    app,
    resources={r"/api/*": {"origins": _allowed_origins}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# ── Conexão Supabase ──────────────────────────────────────────────────────────

def get_db():
    conn = psycopg2.connect(dsn=DATABASE_URL)
    conn.autocommit = False
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Sintomas (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            subtipo TEXT,
            descricao TEXT,
            inicio TIMESTAMP NOT NULL,
            fim TIMESTAMP,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


try:
    init_db()
except Exception as e:
    print(f"[WARN] init_db falhou: {e}")

# ── Decorator de autenticação ─────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            return jsonify({"error": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated


# ── Rotas de Autenticação ─────────────────────────────────────────────────────
@app.route("/api/me", methods=["GET"])
def me():
    if "usuario_id" in session:
        try:
            conn = get_db()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT id, nome, email FROM Usuarios WHERE id = %s", (session["usuario_id"],))
            row = cursor.fetchone()
            conn.close()
            if row:
                return jsonify({"id": row["id"], "nome": row["nome"], "email": row["email"]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Não logado"}), 401


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email", "").strip().lower()
    senha = data.get("senha", "")
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, nome, email, senha_hash FROM Usuarios WHERE email = %s", (email,))
        row = cursor.fetchone()
        conn.close()
        if row and check_password_hash(row["senha_hash"], senha):
            session["usuario_id"] = row["id"]
            session["usuario_nome"] = row["nome"]
            session.permanent = True
            return jsonify({"message": "Login realizado com sucesso",
                            "user": {"id": row["id"], "nome": row["nome"], "email": row["email"]}})
        else:
            return jsonify({"error": "E-mail ou senha incorretos"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cadastro", methods=["POST"])
def cadastro():
    data = request.json
    nome  = data.get("nome", "").strip()
    email = data.get("email", "").strip().lower()
    senha = data.get("senha", "")
    if not nome or not email or not senha:
        return jsonify({"error": "Preencha todos os campos"}), 400
    if len(senha) < 6:
        return jsonify({"error": "A senha deve ter pelo menos 6 caracteres"}), 400
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("INSERT INTO Usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)",
                       (nome, email, generate_password_hash(senha)))
        conn.commit()
        conn.close()
        return jsonify({"message": "Conta criada com sucesso!"}), 201
    except psycopg2.IntegrityError:
        return jsonify({"error": "E-mail já cadastrado"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/usuario", methods=["PUT"])
@login_required
def update_usuario():
    data = request.json
    nome = data.get("nome")
    email = data.get("email")
    if not nome or not email:
        return jsonify({"error": "Nome e e-mail são obrigatórios"}), 400
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("UPDATE Usuarios SET nome=%s, email=%s WHERE id=%s",
                       (nome, email, session["usuario_id"]))
        conn.commit()
        conn.close()
        session["usuario_nome"] = nome
        return jsonify({"message": "Perfil atualizado com sucesso", "nome": nome, "email": email})
    except psycopg2.IntegrityError:
        return jsonify({"error": "Este e-mail já está em uso por outro usuário"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/usuario/senha", methods=["PUT"])
@login_required
def update_senha():
    data = request.json
    senha_atual = data.get("senha_atual")
    senha_nova = data.get("senha_nova")
    if not senha_atual or not senha_nova:
        return jsonify({"error": "Preencha todos os campos"}), 400
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT senha_hash FROM Usuarios WHERE id = %s", (session["usuario_id"],))
        row = cursor.fetchone()
        if row and check_password_hash(row["senha_hash"], senha_atual):
            cursor.execute("UPDATE Usuarios SET senha_hash=%s WHERE id=%s",
                           (generate_password_hash(senha_nova), session["usuario_id"]))
            conn.commit()
            conn.close()
            return jsonify({"message": "Senha atualizada com sucesso"})
        else:
            conn.close()
            return jsonify({"error": "Senha atual incorreta"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logout realizado com sucesso"})


@app.route("/api/sintomas/calendario")
@login_required
def api_calendario_info():
    ano = int(request.args.get("ano", date.today().year))
    mes = int(request.args.get("mes", date.today().month))
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT inicio, fim FROM Sintomas
            WHERE usuario_id = %s
            AND (TO_CHAR(inicio, 'YYYY-MM') <= %s
                AND (fim IS NULL OR TO_CHAR(fim, 'YYYY-MM') >= %s))
        """, (session["usuario_id"], f"{ano}-{mes:02d}", f"{ano}-{mes:02d}"))
        rows = cursor.fetchall()
        calendario = {}
        for row in rows:
            ini_str = row["inicio"].strftime("%Y-%m-%d")
            fim_str = row["fim"].strftime("%Y-%m-%d") if row["fim"] else ini_str
            try:
                ini_dt = datetime.strptime(ini_str, "%Y-%m-%d").date()
                fim_dt = datetime.strptime(fim_str, "%Y-%m-%d").date()
                curr = ini_dt
                while curr <= fim_dt:
                    if curr.year == ano and curr.month == mes:
                        d_str = curr.strftime("%Y-%m-%d")
                        calendario[d_str] = calendario.get(d_str, 0) + 1
                    curr += timedelta(days=1)
            except Exception:
                continue
        conn.close()
        return jsonify(calendario)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sintomas/dia")
@login_required
def api_sintomas_dia():
    data_sel = request.args.get("data")
    if not data_sel:
        return jsonify({"error": "Data não informada"}), 400
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, tipo, subtipo, descricao, inicio, fim FROM Sintomas
            WHERE usuario_id = %s
            AND ((fim IS NULL AND TO_CHAR(inicio, 'YYYY-MM-DD') = %s)
                OR (fim IS NOT NULL
                    AND TO_CHAR(inicio, 'YYYY-MM-DD') <= %s
                    AND TO_CHAR(fim, 'YYYY-MM-DD') >= %s))
            ORDER BY inicio
        """, (session["usuario_id"], data_sel, data_sel, data_sel))
        sintomas = cursor.fetchall()
        conn.close()
        return jsonify(sintomas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sintomas", methods=["POST"])
@login_required
def api_adicionar_sintoma():
    data = request.json
    tipo      = data.get("tipo", "")
    subtipo   = data.get("subtipo")
    descricao = data.get("descricao")
    inicio    = data.get("inicio")
    fim       = data.get("fim")
    if not tipo or not inicio:
        return jsonify({"error": "Tipo e início são obrigatórios"}), 400
    try:
        agora = datetime.now()
        um_ano_atras = agora - timedelta(days=365)
        try:
            ini_dt = datetime.fromisoformat(inicio.replace('Z', '+00:00')) if 'T' in inicio else datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return jsonify({"error": "Formato de data de início inválido"}), 400
        if ini_dt.replace(tzinfo=None) > agora + timedelta(minutes=5):
            return jsonify({"error": "A data de início não pode ser futura"}), 400
        if ini_dt.replace(tzinfo=None) < um_ano_atras:
            return jsonify({"error": "O registro é limitado a no máximo 1 ano atrás"}), 400
        if fim:
            try:
                fim_dt = datetime.fromisoformat(fim.replace('Z', '+00:00')) if 'T' in fim else datetime.strptime(fim, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return jsonify({"error": "Formato de data de fim inválido"}), 400
            if fim_dt.replace(tzinfo=None) < ini_dt.replace(tzinfo=None):
                return jsonify({"error": "A data de término não pode ser anterior à de início"}), 400
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("INSERT INTO Sintomas (usuario_id, tipo, subtipo, descricao, inicio, fim) VALUES (%s, %s, %s, %s, %s, %s)",
                       (session["usuario_id"], tipo, subtipo, descricao, inicio, fim))
        conn.commit()
        conn.close()
        return jsonify({"message": "Sintoma adicionado com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sintomas/<int:sintoma_id>", methods=["PUT", "DELETE"])
@login_required
def api_sintoma_detail(sintoma_id):
    if request.method == "DELETE":
        try:
            conn = get_db()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("DELETE FROM Sintomas WHERE id=%s AND usuario_id=%s", (sintoma_id, session["usuario_id"]))
            conn.commit()
            conn.close()
            return jsonify({"message": "Sintoma excluído"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM Sintomas WHERE id=%s AND usuario_id=%s", (sintoma_id, session["usuario_id"]))
        sintoma_atual = cursor.fetchone()
        if not sintoma_atual:
            conn.close()
            return jsonify({"error": "Sintoma não encontrado"}), 404
        tipo      = data.get("tipo", sintoma_atual["tipo"])
        subtipo   = data.get("subtipo", sintoma_atual["subtipo"])
        descricao = data.get("descricao", sintoma_atual["descricao"])
        inicio    = data.get("inicio", sintoma_atual["inicio"])
        fim       = data.get("fim", sintoma_atual["fim"])
        cursor.execute("""UPDATE Sintomas SET tipo=%s, subtipo=%s, descricao=%s,
                         inicio=%s, fim=%s, atualizado_em=CURRENT_TIMESTAMP
                         WHERE id=%s AND usuario_id=%s""",
                       (tipo, subtipo, descricao, inicio, fim, sintoma_id, session["usuario_id"]))
        conn.commit()
        conn.close()
        return jsonify({"message": "Sintoma atualizado"})
    except Exception as e:
        if 'conn' in locals(): conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/api/sintomas/mes/<int:ano>/<int:mes>")
@login_required
def api_sintomas_mes(ano, mes):
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        mes_formatado = f"{ano}-{mes:02d}"
        cursor.execute("""
            SELECT id, tipo, subtipo, descricao, inicio, fim FROM Sintomas
            WHERE usuario_id = %s
            AND (TO_CHAR(inicio, 'YYYY-MM') <= %s
                AND (fim IS NULL OR TO_CHAR(fim, 'YYYY-MM') >= %s))
            ORDER BY inicio
        """, (session["usuario_id"], mes_formatado, mes_formatado))
        colunas = [desc[0] for desc in cursor.description]
        data = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)

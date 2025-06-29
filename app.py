import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import ldap
from ldap.filter import filter_format
from ldap_config import LDAP_CONFIG

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
UPLOAD_BASE = 'uploads'

# Configuration des groupes et permissions
GROUP_PERMISSIONS = {
    'admin': {
        'allowed_formats': ['txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif'],
        'upload_path': 'uploads/admin',
        'can_view_statistics': True,
        'can_manage_users': True
    },
    'uploader': {
        'allowed_formats': ['txt', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'],
        'upload_path': 'uploads/uploader',
        'can_view_statistics': False,
        'can_manage_users': False
    },
    'viewer': {
        'allowed_formats': ['txt', 'pdf'],
        'upload_path': 'uploads/viewer',
        'can_view_statistics': False,
        'can_manage_users': False
    }
}

def connect_ldap():
    """Établit une connexion LDAP"""
    try:
        ldap_client = ldap.initialize(LDAP_CONFIG['server'])
        ldap_client.set_option(ldap.OPT_REFERRALS, 0)
        ldap_client.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
        ldap_client.set_option(ldap.OPT_TIMEOUT, 10)
        ldap_client.simple_bind_s(LDAP_CONFIG['bind_dn'], LDAP_CONFIG['bind_password'])
        return ldap_client
    except ldap.SERVER_DOWN:
        print("Erreur: Impossible de se connecter au serveur LDAP")
        return None
    except ldap.INVALID_CREDENTIALS:
        print("Erreur: Identifiants LDAP invalides")
        return None
    except Exception as e:
        print(f"Erreur de connexion LDAP: {e}")
        return None

def authenticate_user(username, password):
    """Authentifie un utilisateur via LDAP"""
    try:
        ldap_client = connect_ldap()
        if not ldap_client:
            return None, "Erreur de connexion au serveur LDAP"
        
        # Recherche de l'utilisateur
        user_filter = f"(&{LDAP_CONFIG['user_filter']}(uid={username}))"
        user_search = ldap_client.search_s(
            LDAP_CONFIG['user_search_base'],
            ldap.SCOPE_SUBTREE,
            user_filter,
            LDAP_CONFIG['user_attributes']
        )
        
        if not user_search:
            return None, "Utilisateur non trouvé"
        
        user_dn = user_search[0][0]
        user_info = user_search[0][1]
        
        # Tentative d'authentification
        try:
            ldap_client.simple_bind_s(user_dn, password)
            
            # Récupération des groupes
            groups = []
            if 'memberOf' in user_info:
                for group_dn in user_info['memberOf']:
                    if isinstance(group_dn, bytes):
                        group_dn = group_dn.decode('utf-8')
                    # Extraire le nom du groupe du DN
                    group_name = group_dn.split(',')[0].split('=')[1]
                    groups.append(group_name)
            
            # Récupération du nom d'affichage
            display_name = username
            if 'cn' in user_info:
                cn_value = user_info['cn'][0]
                if isinstance(cn_value, bytes):
                    display_name = cn_value.decode('utf-8')
                else:
                    display_name = cn_value
            
            return {
                'username': username,
                'display_name': display_name,
                'groups': groups
            }, None
            
        except ldap.INVALID_CREDENTIALS:
            return None, "Mot de passe incorrect"
            
    except Exception as e:
        print(f"Erreur d'authentification: {e}")
        return None, f"Erreur d'authentification: {str(e)}"

def get_user_groups(username):
    """Récupère les groupes d'un utilisateur depuis LDAP"""
    try:
        ldap_client = connect_ldap()
        if not ldap_client:
            return []
        
        user_filter = f"(&{LDAP_CONFIG['user_filter']}(uid={username}))"
        user_search = ldap_client.search_s(
            LDAP_CONFIG['user_search_base'],
            ldap.SCOPE_SUBTREE,
            user_filter,
            ['memberOf']
        )
        
        if not user_search:
            return []
        
        user_info = user_search[0][1]
        groups = []
        
        if 'memberOf' in user_info:
            for group_dn in user_info['memberOf']:
                if isinstance(group_dn, bytes):
                    group_dn = group_dn.decode('utf-8')
                group_name = group_dn.split(',')[0].split('=')[1]
                groups.append(group_name)
        
        return groups
        
    except Exception as e:
        print(f"Erreur de récupération des groupes: {e}")
        return []

def allowed_file(filename, user_groups):
    ext = os.path.splitext(filename)[1].lower()
    allowed = set()
    for group in user_groups:
        allowed.update(GROUP_PERMISSIONS.get(group, {}).get('allowed_formats', []))
    return ext in allowed

def get_upload_path(username, user_groups):
    # Chemin dynamique selon le premier groupe (ou username)
    group = user_groups[0] if user_groups else username
    if group in GROUP_PERMISSIONS:
        return GROUP_PERMISSIONS[group]['upload_path']
    else:
        path = os.path.join(UPLOAD_BASE, secure_filename(group))
    if not os.path.exists(path):
        return None
    return path

def log_global_action(user, action, detail):
    with open('all_actions.log', 'a', encoding='utf-8') as logf:
        logf.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{user},{action},{detail}\n")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_info, error = authenticate_user(username, password)
        
        if user_info:
            session['username'] = username
            session['display_name'] = user_info['display_name']
            session['groups'] = user_info['groups']
            log_global_action(username, 'login_success', f"groups={user_info['groups']}")
            return redirect(url_for('dashboard'))
        else:
            flash(f'Échec de connexion: {error}', 'error')
            log_global_action(username, 'login_failed', error)
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    groups = session.get('groups', [])
    upload_path = get_upload_path(username, groups)
    files = os.listdir(upload_path) if upload_path and os.path.exists(upload_path) else []
    actions = session.get('actions', [])
    
    show_create_folder = False
    show_edit_upload_path = False
    all_groups = []
    folder_actions = []
    
    if 'admin' in groups and request.args.get('create_folder') == '1':
        show_create_folder = True
        # Liste des groupes LDAP
        all_groups_set = set()
        for user in GROUP_PERMISSIONS.keys():
            all_groups_set.update(GROUP_PERMISSIONS[user].get('allowed_formats', []))
        all_groups_set.discard('admin')
        all_groups = sorted(all_groups_set)
        
        # Lecture de l'historique des créations de dossier
        log_path = 'create_folder.log'
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 6:
                        folder_actions.append({
                            'date': parts[0],
                            'user': parts[1],
                            'path': parts[2],
                            'type': parts[3],
                            'msg': parts[4],
                            'desc': parts[5]
                        })
    elif 'admin' in groups and request.args.get('edit_upload_path') == '1':
        show_edit_upload_path = True
        all_groups_set = set()
        for user in GROUP_PERMISSIONS.keys():
            all_groups_set.update(GROUP_PERMISSIONS[user].get('allowed_formats', []))
        all_groups_set.discard('admin')
        all_groups = sorted(all_groups_set)
    
    return render_template('dashboard.html', 
                         username=username, 
                         display_name=session.get('display_name', username),
                         groups=groups, 
                         files=files, 
                         actions=actions,
                         show_create_folder=show_create_folder, 
                         show_edit_upload_path=show_edit_upload_path, 
                         all_groups=all_groups, 
                         folder_actions=folder_actions)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    groups = session.get('groups', [])
    upload_path = get_upload_path(username, groups)
    
    if upload_path is None:
        flash("Le dossier d'upload n'existe pas sur le serveur.", 'error')
        if 'actions' not in session:
            session['actions'] = []
        session['actions'].append({'type': 'error', 'msg': "Dossier d'upload inexistant pour le groupe.", 'time': datetime.now().strftime('%H:%M:%S')})
        session.modified = True
        log_global_action(username, 'upload_error', f"groupe={groups}, path={upload_path}, msg=Dossier d'upload inexistant")
        return redirect(url_for('dashboard'))
    
    desc = request.form.get('description', '').strip()
    if 'actions' not in session:
        session['actions'] = []
    
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné', 'error')
        session['actions'].append({'type': 'error', 'msg': 'Aucun fichier sélectionné', 'time': datetime.now().strftime('%H:%M:%S')})
        session.modified = True
        log_global_action(username, 'upload_error', f"groupe={groups}, path={upload_path}, msg=Aucun fichier sélectionné")
        return redirect(url_for('dashboard'))
    
    files = request.files.getlist('file')
    uploaded = 0
    refused = []
    
    for file in files:
        if file.filename == '':
            continue
        if not allowed_file(file.filename, groups):
            refused.append(file.filename)
            continue
        
        filename = secure_filename(file.filename)
        file.save(os.path.join(upload_path, filename))
        
        # Log de l'upload avec taille du fichier
        file_size = os.path.getsize(os.path.join(upload_path, filename))
        log_line = f"{filename}, {file_size}, {desc.replace(',', ' ')}, {upload_path}"
        log_global_action(username, 'upload_success', log_line)
        uploaded += 1
    
    if uploaded > 0 and not refused:
        msg = f"{uploaded} fichier(s) uploadé(s) avec succès"
        if desc:
            msg += f" (description : {desc})"
        flash(f"{uploaded} fichier(s) uploadé(s) avec succès !", 'success')
        session['actions'].append({'type': 'success', 'msg': msg, 'time': datetime.now().strftime('%H:%M:%S')})
    elif uploaded > 0 and refused:
        msg = f"{uploaded} fichier(s) uploadé(s), refusé(s) : {', '.join(refused)}"
        if desc:
            msg += f" (description : {desc})"
        flash(f"{uploaded} fichier(s) uploadé(s), mais refusé(s) : {', '.join(refused)} (format non autorisé)", 'warning')
        session['actions'].append({'type': 'warning', 'msg': msg, 'time': datetime.now().strftime('%H:%M:%S')})
        log_global_action(username, 'upload_partial', f"ok={uploaded}, refused={refused}, desc={desc}, path={upload_path}")
    elif uploaded == 0 and refused:
        msg = f"Aucun fichier uploadé. Refusé(s) : {', '.join(refused)}"
        if desc:
            msg += f" (description : {desc})"
        flash(f"Aucun fichier uploadé. Fichiers refusés : {', '.join(refused)} (format non autorisé)", 'error')
        session['actions'].append({'type': 'error', 'msg': msg, 'time': datetime.now().strftime('%H:%M:%S')})
        log_global_action(username, 'upload_refused', f"refused={refused}, desc={desc}, path={upload_path}")
    else:
        msg = 'Aucun fichier uploadé.'
        if desc:
            msg += f" (description : {desc})"
        flash('Aucun fichier uploadé.', 'error')
        session['actions'].append({'type': 'error', 'msg': msg, 'time': datetime.now().strftime('%H:%M:%S')})
        log_global_action(username, 'upload_empty', f"desc={desc}, path={upload_path}")
    
    session.modified = True
    return redirect(url_for('dashboard'))

@app.route('/download/<path:group>/<filename>')
def download_file(group, filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Sécurité : vérifier que le groupe fait partie des groupes de l'utilisateur
    if group not in [secure_filename(g) for g in session.get('groups', [])]:
        flash('Accès refusé')
        return redirect(url_for('dashboard'))
    
    path = os.path.join(UPLOAD_BASE, group)
    return send_from_directory(path, filename, as_attachment=True)

@app.route('/logout')
def logout():
    if 'username' in session:
        log_global_action(session['username'], 'logout', "")
    session.clear()
    return redirect(url_for('login'))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    if 'username' not in session:
        return redirect(url_for('login'))
    session['actions'] = []
    log_global_action(session['username'], 'clear_upload_history', "")
    flash('Historique effacé.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/create_folder', methods=['GET', 'POST'])
def create_folder():
    if 'username' not in session or 'admin' not in session.get('groups', []):
        flash("Accès réservé au groupe admin.", 'error')
        return redirect(url_for('dashboard'))
    
    all_groups = set()
    for user in GROUP_PERMISSIONS.keys():
        all_groups.update(GROUP_PERMISSIONS[user].get('allowed_formats', []))
    all_groups.discard('admin')
    all_groups = sorted(all_groups)
    
    if request.method == 'POST':
        path = request.form.get('path', '').strip()
        restricted = request.form.get('restricted') == 'on'
        allowed_groups = request.form.getlist('allowed_groups') if restricted else []
        description = request.form.get('description', '').strip()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user = session['username']
        log_path = 'create_folder.log'
        
        if not path:
            msg = 'Le chemin du dossier est obligatoire.'
            flash(msg, 'error')
            log_global_action(user, 'create_folder_error', f"path={path}, msg={msg}, desc={description}")
            with open(log_path, 'a', encoding='utf-8') as logf:
                logf.write(f"{now},{user},{path},error,{msg},{description}\n")
            return render_template('create_folder.html', all_groups=all_groups)
        
        try:
            os.makedirs(path, exist_ok=False)
            msg = 'Dossier créé avec succès.'
            flash(msg, 'success')
            log_global_action(user, 'create_folder_success', f"path={path}, msg={msg}, desc={description}")
            with open(log_path, 'a', encoding='utf-8') as logf:
                logf.write(f"{now},{user},{path},success,{msg},{description}\n")
            return redirect(url_for('dashboard', create_folder=1))
        except FileExistsError:
            msg = 'Ce dossier existe déjà.'
            flash(msg, 'error')
            log_global_action(user, 'create_folder_error', f"path={path}, msg={msg}, desc={description}")
            with open(log_path, 'a', encoding='utf-8') as logf:
                logf.write(f"{now},{user},{path},error,{msg},{description}\n")
            return render_template('create_folder.html', all_groups=all_groups)
        except Exception as e:
            msg = f'Erreur lors de la création du dossier : {e}'
            flash(msg, 'error')
            log_global_action(user, 'create_folder_error', f"path={path}, msg={msg}, desc={description}")
            with open(log_path, 'a', encoding='utf-8') as logf:
                logf.write(f"{now},{user},{path},error,{msg},{description}\n")
            return render_template('create_folder.html', all_groups=all_groups)
    
    return render_template('create_folder.html', all_groups=all_groups)

@app.route('/clear_folder_history', methods=['POST'])
def clear_folder_history():
    if 'username' not in session or 'admin' not in session.get('groups', []):
        flash("Accès réservé au groupe admin.", 'error')
        return redirect(url_for('dashboard'))
    open('create_folder.log', 'w').close()
    log_global_action(session['username'], 'clear_folder_history', "")
    flash('Historique des créations de dossier effacé.', 'success')
    return redirect(url_for('dashboard', create_folder=1))

@app.route('/edit_upload_path', methods=['POST'])
def edit_upload_path():
    if 'username' not in session or 'admin' not in session.get('groups', []):
        flash("Accès réservé au groupe admin.", 'error')
        return redirect(url_for('dashboard'))
    
    path = request.form.get('edit_path', '').strip()
    groups = request.form.getlist('edit_groups')
    description = request.form.get('edit_description', '').strip()
    
    if not path:
        flash('Le chemin est obligatoire.', 'error')
        log_global_action(session['username'], 'edit_upload_path_error', f"path={path}, msg=chemin obligatoire, desc={description}")
        return redirect(url_for('dashboard', edit_upload_path=1))
    
    # Ici, on simule la modification (pas de persistance réelle)
    flash('Chemin d\'upload modifié (simulation).', 'success')
    log_global_action(session['username'], 'edit_upload_path', f"path={path}, groupes={groups}, desc={description}")
    return redirect(url_for('dashboard', edit_upload_path=1))

@app.route('/statistics')
def statistics():
    if 'username' not in session or 'admin' not in session.get('groups', []):
        flash("Accès réservé au groupe admin.", 'error')
        return redirect(url_for('dashboard'))
    
    # Lecture du fichier de log pour analyser les statistiques
    stats = {
        'total_uploads': 0,
        'total_size': 0,
        'uploads_by_user': {},
        'uploads_by_group': {},
        'uploads_by_date': {},
        'uploads_by_type': {},
        'recent_uploads': [],
        'top_users': [],
        'top_groups': [],
        'top_file_types': []
    }
    
    if os.path.exists('all_actions.log'):
        with open('all_actions.log', 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 4 and parts[2] == 'upload_success':
                    # Format: date, user, action, filename, size, description, path
                    if len(parts) >= 5:
                        try:
                            date = parts[0]
                            user = parts[1]
                            filename = parts[3]
                            size = int(parts[4]) if parts[4].strip().isdigit() else 0
                            description = parts[5] if len(parts) > 5 else ''
                            path = parts[6] if len(parts) > 6 else ''
                            
                            # Statistiques générales
                            stats['total_uploads'] += 1
                            stats['total_size'] += size
                            
                            # Par utilisateur
                            if user not in stats['uploads_by_user']:
                                stats['uploads_by_user'][user] = {'count': 0, 'size': 0}
                            stats['uploads_by_user'][user]['count'] += 1
                            stats['uploads_by_user'][user]['size'] += size
                            
                            # Par date
                            date_key = date.split(' ')[0]  # Juste la date
                            if date_key not in stats['uploads_by_date']:
                                stats['uploads_by_date'][date_key] = {'count': 0, 'size': 0}
                            stats['uploads_by_date'][date_key]['count'] += 1
                            stats['uploads_by_date'][date_key]['size'] += size
                            
                            # Par type de fichier
                            file_ext = os.path.splitext(filename)[1].lower()
                            if file_ext not in stats['uploads_by_type']:
                                stats['uploads_by_type'][file_ext] = {'count': 0, 'size': 0}
                            stats['uploads_by_type'][file_ext]['count'] += 1
                            stats['uploads_by_type'][file_ext]['size'] += size
                            
                            # Derniers uploads
                            stats['recent_uploads'].append({
                                'date': date,
                                'user': user,
                                'filename': filename,
                                'size': size,
                                'description': description,
                                'path': path
                            })
                            
                            # Déterminer le groupe basé sur le chemin
                            group = "Autre"
                            for g in GROUP_PERMISSIONS.keys():
                                if g in path:
                                    group = g
                            
                            if group not in stats['uploads_by_group']:
                                stats['uploads_by_group'][group] = {'count': 0, 'size': 0}
                            stats['uploads_by_group'][group]['count'] += 1
                            stats['uploads_by_group'][group]['size'] += size
                            
                        except (ValueError, IndexError):
                            continue
    
    # Trier les listes
    stats['recent_uploads'] = sorted(stats['recent_uploads'], key=lambda x: x['date'], reverse=True)[:20]
    
    # Top utilisateurs
    stats['top_users'] = sorted(stats['uploads_by_user'].items(), 
                               key=lambda x: x[1]['count'], reverse=True)[:10]
    
    # Top groupes
    stats['top_groups'] = sorted(stats['uploads_by_group'].items(), 
                                key=lambda x: x[1]['count'], reverse=True)
    
    # Top types de fichiers
    stats['top_file_types'] = sorted(stats['uploads_by_type'].items(), 
                                    key=lambda x: x[1]['count'], reverse=True)[:10]
    
    # Statistiques par date (derniers 30 jours)
    from datetime import datetime, timedelta
    last_30_days = {}
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        last_30_days[date] = stats['uploads_by_date'].get(date, {'count': 0, 'size': 0})
    
    stats['daily_stats'] = sorted(last_30_days.items(), reverse=True)
    
    return render_template('statistics.html', stats=stats)

if __name__ == '__main__':
    # Créer les dossiers d'upload s'ils n'existent pas
    for group_config in GROUP_PERMISSIONS.values():
        upload_path = group_config['upload_path']
        if not os.path.exists(upload_path):
            os.makedirs(upload_path, exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
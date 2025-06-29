# Portail Upload avec Authentification LDAP

Une application Flask moderne pour l'upload de fichiers avec authentification LDAP et gestion des permissions par groupe.

## 🚀 Fonctionnalités

- **Authentification LDAP** : Connexion à un vrai serveur LDAP
- **Gestion des groupes** : Permissions basées sur les groupes LDAP
- **Upload de fichiers** : Support multi-fichiers avec prévisualisation
- **Interface moderne** : Design responsive et professionnel
- **Statistiques** : Tableaux de bord pour les administrateurs
- **Logs détaillés** : Historique complet des actions

## 📋 Prérequis

- Python 3.7+
- Serveur LDAP (Active Directory, OpenLDAP, etc.)
- Accès administrateur au serveur LDAP

## 🔧 Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd uploadNew
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer LDAP**
Modifiez le fichier `ldap_config.py` avec vos paramètres LDAP :

```python
LDAP_CONFIG = {
    'server': 'ldap://votre-serveur-ldap.com:389',
    'base_dn': 'dc=votre-domaine,dc=com',
    'bind_dn': 'cn=admin,dc=votre-domaine,dc=com',
    'bind_password': 'votre-mot-de-passe-admin',
    'user_search_base': 'ou=Users,dc=votre-domaine,dc=com',
    'group_search_base': 'ou=Groups,dc=votre-domaine,dc=com',
    'user_filter': '(objectClass=person)',
    'group_filter': '(objectClass=groupOfNames)',
    'user_attributes': ['dn', 'cn', 'uid', 'memberOf', 'mail'],
    'group_attributes': ['dn', 'cn', 'member']
}
```

## 🏃‍♂️ Lancement

```bash
python app.py
```

L'application sera accessible à l'adresse : `http://localhost:5000`

## 👥 Configuration des Groupes

L'application utilise les groupes LDAP pour définir les permissions :

### Groupe `admin`
- **Formats autorisés** : Tous les formats
- **Permissions** : Accès aux statistiques, gestion des dossiers
- **Chemin d'upload** : `uploads/admin`

### Groupe `uploader`
- **Formats autorisés** : txt, pdf, doc, docx, jpg, jpeg, png
- **Permissions** : Upload de fichiers uniquement
- **Chemin d'upload** : `uploads/uploader`

### Groupe `viewer`
- **Formats autorisés** : txt, pdf
- **Permissions** : Consultation uniquement
- **Chemin d'upload** : `uploads/viewer`

## 🔐 Configuration LDAP

### Active Directory
```python
LDAP_CONFIG = {
    'server': 'ldap://dc.company.com:389',
    'base_dn': 'dc=company,dc=com',
    'bind_dn': 'cn=admin,dc=company,dc=com',
    'bind_password': 'admin_password',
    'user_search_base': 'ou=Users,dc=company,dc=com',
    'group_search_base': 'ou=Groups,dc=company,dc=com',
    'user_filter': '(objectClass=user)',
    'group_filter': '(objectClass=group)',
    'user_attributes': ['dn', 'cn', 'sAMAccountName', 'memberOf', 'mail'],
    'group_attributes': ['dn', 'cn', 'member']
}
```

### OpenLDAP
```python
LDAP_CONFIG = {
    'server': 'ldap://ldap.company.com:389',
    'base_dn': 'dc=company,dc=com',
    'bind_dn': 'cn=admin,dc=company,dc=com',
    'bind_password': 'admin_password',
    'user_search_base': 'ou=people,dc=company,dc=com',
    'group_search_base': 'ou=groups,dc=company,dc=com',
    'user_filter': '(objectClass=person)',
    'group_filter': '(objectClass=groupOfNames)',
    'user_attributes': ['dn', 'cn', 'uid', 'memberOf', 'mail'],
    'group_attributes': ['dn', 'cn', 'member']
}
```

## 📁 Structure des Dossiers

```
uploadNew/
├── app.py                 # Application principale
├── ldap_config.py         # Configuration LDAP
├── requirements.txt       # Dépendances Python
├── README.md             # Documentation
├── templates/            # Templates HTML
│   ├── login.html
│   ├── dashboard.html
│   └── statistics.html
├── static/               # Fichiers statiques
│   ├── style.css
│   └── script.js
└── uploads/              # Dossiers d'upload
    ├── admin/
    ├── uploader/
    └── viewer/
```

## 🔍 Dépannage

### Erreur de connexion LDAP
- Vérifiez l'adresse du serveur LDAP
- Vérifiez les identifiants d'administration
- Vérifiez que le port LDAP est accessible

### Utilisateur non trouvé
- Vérifiez la base de recherche des utilisateurs
- Vérifiez le filtre de recherche
- Vérifiez que l'utilisateur existe dans LDAP

### Problème d'authentification
- Vérifiez que l'utilisateur peut se connecter avec ses identifiants
- Vérifiez les permissions LDAP
- Vérifiez la configuration des groupes

## 📊 Logs

L'application génère plusieurs fichiers de logs :

- `all_actions.log` : Historique complet des actions
- `create_folder.log` : Historique des créations de dossiers

## 🔒 Sécurité

- Les mots de passe ne sont jamais stockés
- Validation des types de fichiers
- Contrôle d'accès basé sur les groupes
- Sanitisation des noms de fichiers
- Logs de sécurité

## 🤝 Contribution

Pour contribuer au projet :

1. Fork le repository
2. Créez une branche pour votre fonctionnalité
3. Committez vos changements
4. Poussez vers la branche
5. Créez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

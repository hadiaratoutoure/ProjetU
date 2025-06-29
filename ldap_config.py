# Configuration LDAP - À modifier selon votre serveur LDAP
LDAP_CONFIG = {
    # Serveur LDAP
    'server': 'ldap://your-ldap-server.com:389',  # Remplacez par votre serveur LDAP
    
    # Base DN de votre annuaire
    'base_dn': 'dc=example,dc=com',  # Remplacez par votre base DN
    
    # Compte d'administration pour les recherches
    'bind_dn': 'cn=admin,dc=example,dc=com',  # Remplacez par votre DN d'administration
    'bind_password': 'admin_password',  # Remplacez par votre mot de passe
    
    # Base de recherche des utilisateurs
    'user_search_base': 'ou=users,dc=example,dc=com',  # Remplacez par votre OU des utilisateurs
    
    # Base de recherche des groupes
    'group_search_base': 'ou=groups,dc=example,dc=com',  # Remplacez par votre OU des groupes
    
    # Filtres de recherche
    'user_filter': '(objectClass=person)',
    'group_filter': '(objectClass=groupOfNames)',
    
    # Attributs à récupérer
    'user_attributes': ['dn', 'cn', 'uid', 'memberOf', 'mail'],
    'group_attributes': ['dn', 'cn', 'member']
}

# Exemple de configuration pour différents types de serveurs LDAP :

# Active Directory
# LDAP_CONFIG = {
#     'server': 'ldap://dc.company.com:389',
#     'base_dn': 'dc=company,dc=com',
#     'bind_dn': 'cn=admin,dc=company,dc=com',
#     'bind_password': 'admin_password',
#     'user_search_base': 'ou=Users,dc=company,dc=com',
#     'group_search_base': 'ou=Groups,dc=company,dc=com',
#     'user_filter': '(objectClass=user)',
#     'group_filter': '(objectClass=group)',
#     'user_attributes': ['dn', 'cn', 'sAMAccountName', 'memberOf', 'mail'],
#     'group_attributes': ['dn', 'cn', 'member']
# }

# OpenLDAP
# LDAP_CONFIG = {
#     'server': 'ldap://ldap.company.com:389',
#     'base_dn': 'dc=company,dc=com',
#     'bind_dn': 'cn=admin,dc=company,dc=com',
#     'bind_password': 'admin_password',
#     'user_search_base': 'ou=people,dc=company,dc=com',
#     'group_search_base': 'ou=groups,dc=company,dc=com',
#     'user_filter': '(objectClass=person)',
#     'group_filter': '(objectClass=groupOfNames)',
#     'user_attributes': ['dn', 'cn', 'uid', 'memberOf', 'mail'],
#     'group_attributes': ['dn', 'cn', 'member']
# } 
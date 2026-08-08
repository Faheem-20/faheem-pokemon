import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open(r'c:\Users\simha\Downloads\Pokemon_Nexus_Complete_Project\Pokeman\scratch\original_battle.html', 'r', encoding='utf-16') as f:
    content = f.read()

# Find style block
start_css = content.find('/* NAVBAR */')
end_css = content.find('/* MAIN CONTAINER SETUP */')
print('=== ORIGINAL CSS ===')
print(content[start_css:end_css])

# Find HTML block
start_html = content.find('<!-- NAVBAR -->')
end_html = content.find('<main class="page">')
print('=== ORIGINAL HTML ===')
print(content[start_html:end_html])

import csv
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from ttkthemes import ThemedTk
from tkinter import ttk
import os
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io



entry_fields = {}
janela_pesquisa = None
janela_cadastro = None
janela_edicao = None
janela_cliente_encontrado = None

scope = ['https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name( os.path.join(os.path.dirname(__file__), 'arquivo.json')
 , scope)
service = build('drive', 'v3', credentials=credentials)

file_id = 'file id'

def download_file_content(file_id):
    request = service.files().get_media(fileId=file_id)
    media = io.BytesIO()
    downloader = MediaIoBaseDownload(media, request)
    done = False
    while done is False:
        _, done = downloader.next_chunk()
    media.seek(0)
    content = media.read().decode('utf-8')
    return content

def upload_modified_content(file_id, modified_content):
    media_body = MediaIoBaseUpload(
        io.BytesIO(modified_content.encode('utf-8')),
        mimetype='text/plain',
        resumable=True
    )
    
    updated_file = service.files().get(fileId=file_id).execute()
    
    updated_file = service.files().update(
        fileId=file_id,
        media_body=media_body
    ).execute()


def pesquisar_cliente():
    global janela_pesquisa, janela_cliente_encontrado

    nome_sobrenome_pesquisa = entry_fields['nome_sobrenome_pesquisa'].get().strip()

    if not nome_sobrenome_pesquisa:
        messagebox.showerror("Campo vazio", "Por favor, digite o nome e sobrenome para pesquisar.")
        return

    content = download_file_content(file_id)

    clientes = []
    for linha in content.split('\n'):
        cliente = linha.strip().split(',')
        if len(cliente) == 6:
            clientes.append(cliente)

    encontrado = False
    cliente_encontrado = None

    for cliente in clientes:
        nome_completo = cliente[0] + " " + cliente[1]
        if nome_sobrenome_pesquisa.upper() == nome_completo.upper():
            encontrado = True
            cliente_encontrado = cliente
            break

    if encontrado:
        mensagem = f"Dados do cliente:\n\n\n      Nome: {cliente_encontrado[0]}\n\n      Sobrenome: {cliente_encontrado[1]}\n\n      Data de Nascimento: {cliente_encontrado[2]}\n\n      Passaporte: {cliente_encontrado[3]}\n\n      Validade do Passaporte: {cliente_encontrado[4]}\n\n      Número de Contato:{cliente_encontrado[5]}"

        janela_cliente_encontrado = tk.Toplevel(janela)
        janela_cliente_encontrado.title("Dados do Cliente")
        label_mensagem = ttk.Label(janela_cliente_encontrado, text=mensagem)
        label_mensagem.pack(padx=20, pady=20)

        botao_editar = ttk.Button(janela_cliente_encontrado, text="Editar", style='Accent.TButton', command=lambda: abrir_tela_edicao_cliente(cliente_encontrado))
        botao_editar.pack(pady=10)

        botao_voltar = ttk.Button(janela_cliente_encontrado, text="Voltar", style='Accent.TButton', command=janela_cliente_encontrado.destroy)
        botao_voltar.pack(pady=10)
    else:
        messagebox.showinfo("Cliente não encontrado", f"O cliente '{nome_sobrenome_pesquisa}' não foi encontrado.")

    janela_pesquisa.destroy()

def abrir_tela_edicao_cliente(cliente):
    global janela_edicao, janela_cliente_encontrado
    janela_edicao = tk.Toplevel(janela)
    janela_edicao.title("Editar Cliente")
    janela_edicao.geometry("330x430")

    fields = ['nome', 'sobrenome', 'data_nascimento', 'passaporte', 'validade_passaporte', 'numero_contato']

    for i, field in enumerate(fields):
        label = ttk.Label(janela_edicao, text=field.capitalize().replace('_', ' ') + ":")
        label.grid(row=i, column=0, padx=0, pady=10)

        if field in ['data_nascimento', 'validade_passaporte']:
            entry = ttk.Entry(janela_edicao)
            if field == 'data_nascimento':
                entry.insert(0, cliente[2])
            elif field == 'validade_passaporte':
                entry.insert(0, cliente[4])
        else:
            entry = ttk.Entry(janela_edicao)
            entry.insert(0, cliente[i])

        entry.grid(row=i, column=1, padx=0, pady=10)
        entry_fields[field] = entry

    botao_salvar = ttk.Button(janela_edicao, text="Salvar Alterações", style='Accent.TButton', command=lambda: salvar_alteracoes(cliente))
    botao_salvar.grid(row=len(fields), column=0, columnspan=1, padx=20, pady=10) 

    botao_excluir = ttk.Button(janela_edicao, text="Excluir Cliente", style='Accent.TButton', command=lambda: excluir_cliente(cliente))
    botao_excluir.grid(row=len(fields) +1, column=0, columnspan=2, padx=0, pady=10)

    botao_voltar = ttk.Button(janela_edicao, text="Voltar", style='Accent.TButton', command=janela_edicao.destroy)
    botao_voltar.grid(row=len(fields), column=1, columnspan=1, padx=0, pady=0)

def salvar_alteracoes(cliente):
    novos_dados = [entry_fields['nome'].get().upper(),
                   entry_fields['sobrenome'].get().upper(),
                   entry_fields['data_nascimento'].get(),
                   entry_fields['passaporte'].get().upper(),
                   entry_fields['validade_passaporte'].get(),
                   entry_fields['numero_contato'].get()]

    content = download_file_content(file_id)
    modified_lines = []

    for linha in content.split('\n'):
        dados_cliente = linha.strip().split(',')
        if len(dados_cliente) == 6:
            nome_completo = dados_cliente[0] + " " + dados_cliente[1]
            cliente_completo = cliente[0] + " " + cliente[1]

            if nome_completo.upper() == cliente_completo.upper():
                modified_line = ','.join(novos_dados)
                modified_lines.append(modified_line)
            else:
                modified_lines.append(linha)
        else:
            modified_lines.append(linha)

    modified_content = '\n'.join(modified_lines)
    upload_modified_content(file_id, modified_content)

    if janela_edicao:
        janela_edicao.destroy()
    if janela_cliente_encontrado:
        janela_cliente_encontrado.destroy()

    messagebox.showinfo("Edição Concluída", "As alterações foram salvas com sucesso.")

def cadastrar_cliente():
    nome = entry_fields['nome'].get().upper()
    sobrenome = entry_fields['sobrenome'].get().upper()
    data_nascimento = entry_fields['data_nascimento'].get()
    passaporte = entry_fields['passaporte'].get().upper()
    validade_passaporte = entry_fields['validade_passaporte'].get()
    numero_contato = entry_fields['numero_contato'].get()
    
    current_content = download_file_content(file_id)
    new_text = f"\n{nome},{sobrenome},{data_nascimento},{passaporte},{validade_passaporte},{numero_contato}"
    modified_content = current_content + new_text
    upload_modified_content(file_id, modified_content)

    mensagem = f"Cliente cadastrado:\nNome: {nome} {sobrenome}\nData de Nascimento: {data_nascimento}\nPassaporte: {passaporte}\nValidade do Passaporte: {validade_passaporte}\nNúmero de Contato: {numero_contato}"
    messagebox.showinfo("Cadastro de Cliente", mensagem)
    janela_cadastro.destroy()

def verificar_validade_passaporte():
    content = download_file_content(file_id)

    passaportes_proximos_vencer = []
    data_atual = datetime.now().date()

    for linha in content.split('\n'):
        dados_cliente = linha.strip().split(',')
        if len(dados_cliente) == 6:
            validade_passaporte_str = dados_cliente[4]
            try:
                validade_passaporte = datetime.strptime(validade_passaporte_str, "%d/%m/%Y").date()
                diferenca_dias = (validade_passaporte - data_atual).days

                if diferenca_dias <= 180:
                    passaportes_proximos_vencer.append((dados_cliente[0], dados_cliente[1], validade_passaporte_str))

            except ValueError:
                pass

    if passaportes_proximos_vencer:
        mensagem = "Passaportes próximos a vencer:\n"
        for nome, sobrenome, validade in passaportes_proximos_vencer:
            mensagem += f"{nome} {sobrenome}: {validade}\n"

        messagebox.showwarning("Passaportes Próximos a Vencer", mensagem)
    else:
        messagebox.showinfo("Validade do Passaporte", "Todos os passaportes estão com a validade ok!")

def abrir_tela_cadastro():
    global janela_cadastro
    janela_cadastro = tk.Toplevel(janela)
    janela_cadastro.title("Cadastro de Cliente")

    fields = ['nome', 'sobrenome', 'data_nascimento', 'passaporte', 'validade_passaporte', 'numero_contato']
    for i, field in enumerate(fields):
        label = ttk.Label(janela_cadastro, text=field.capitalize().replace('_', ' ') + ":")
        label.grid(row=i, column=0, padx=20, pady=20)
        
        if field in ['data_nascimento', 'validade_passaporte']:
            entry = DateEntry(janela_cadastro, date_pattern='dd/mm/yyyy')
        else:
            entry = ttk.Entry(janela_cadastro)
        
        entry.grid(row=i, column=1)
        entry_fields[field] = entry

    botao_cadastrar = ttk.Button(janela_cadastro, text="Cadastrar", style='Accent.TButton', command= cadastrar_cliente)
    botao_cadastrar.grid(row=len(fields), column=0, columnspan=1, padx=0, pady=20)

    botao_voltar = ttk.Button(janela_cadastro, text="Voltar", style='Accent.TButton', command=janela_cadastro.destroy)
    botao_voltar.grid(row=len(fields), column=1, columnspan=1)

def abrir_tela_pesquisa():
    global janela_pesquisa
    janela_pesquisa = tk.Toplevel(janela)
    janela_pesquisa.title("Pesquisa de Cliente")

    label_nome_sobrenome_pesquisa = ttk.Label(janela_pesquisa, text="Nome e Sobrenome:")
    label_nome_sobrenome_pesquisa.grid(row=0, column=0, padx=10,pady=10)
    entry_nome_sobrenome_pesquisa = ttk.Entry(janela_pesquisa)
    entry_nome_sobrenome_pesquisa.grid(row=0, column=1, pady=10)
    entry_fields['nome_sobrenome_pesquisa'] = entry_nome_sobrenome_pesquisa

    botao_pesquisar = ttk.Button(janela_pesquisa, text="Pesquisar",style='Accent.TButton', command=pesquisar_cliente)
    botao_pesquisar.grid(row=1, column=0, columnspan=1, padx=10, pady=10)

    botao_voltar = ttk.Button(janela_pesquisa, text="Voltar", style='Accent.TButton', command=janela_pesquisa.destroy)
    botao_voltar.grid(row=1, column=1, columnspan=2, padx=10, pady=20)

def excluir_cliente(cliente):
    content = download_file_content(file_id)
    
    modified_lines = []
    for linha in content.split('\n'):
        dados_cliente = linha.strip().split(',')
        if len(dados_cliente) == 6:
            nome_completo = dados_cliente[0] + " " + dados_cliente[1]
            cliente_completo = cliente[0] + " " + cliente[1]
            if nome_completo.upper() != cliente_completo.upper():
                modified_lines.append(linha)

    modified_content = '\n'.join(modified_lines)
    upload_modified_content(file_id, modified_content)

    messagebox.showinfo("Cliente Excluído", "O cliente foi excluído com sucesso.")
    janela_edicao.destroy()
    janela_cliente_encontrado.destroy()

root = tk.Tk()
root.title("Chacontour App")
icon_path = 'C:\\Users\\chaco\\OneDrive\\Documents\\Chacontur-app\\chacontour.ico' 
root.iconbitmap(icon_path)

janela = ttk.Frame(root)
root.state('zoomed')
janela.pack(fill="both", expand=True)

theme_file = os.path.join(os.path.dirname(__file__), "azure.tcl")
root.tk.call("source", theme_file)
root.tk.call("set_theme", "dark")

def change_theme():
    if root.tk.call("ttk::style", "theme", "use") == "azure-dark":
        root.tk.call("set_theme", "light")
    else:
        root.tk.call("set_theme", "dark")

botao_cadastro = ttk.Button(janela, text="Cadastro", style='Accent.TButton', command=abrir_tela_cadastro)
botao_cadastro.pack(pady=70, padx=50)

botao_pesquisa = ttk.Button(janela, text="Pesquisa", style='Accent.TButton', command=abrir_tela_pesquisa)
botao_pesquisa.pack(pady=50, padx=50)

botao_verificar = ttk.Button(janela, text="Checar Passaportes", style='Accent.TButton', command=verificar_validade_passaporte)
botao_verificar.pack(pady=50, padx=50)

button = ttk.Checkbutton(janela, text="Alterar", style="Switch.TCheckbutton", command=change_theme)
button.pack(pady=70, padx=50)

janela.mainloop()

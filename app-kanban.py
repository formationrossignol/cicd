#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser
import json
import os
from datetime import datetime
import random

class ActivityLog:
    def __init__(self):
        self.activities = []
    
    def add(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.activities.insert(0, f"[{timestamp}] {message}")
        if len(self.activities) > 100:
            self.activities = self.activities[:100]

class KanbanCard:
    def __init__(self, title, description="", assigned_to="", color="#ffffff"):
        self.title = title
        self.description = description
        self.assigned_to = assigned_to
        self.color = color
        self.id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.avatar_color = self.generate_avatar_color(assigned_to)

    def generate_avatar_color(self, name):
        if not name:
            return "#cccccc"
        
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57",
            "#FF9FF3", "#54A0FF", "#5F27CD", "#00D2D3", "#FF9F43",
            "#FC427B", "#26DE81", "#2D98DA", "#A55EEA", "#FD79A8"
        ]
        index = sum(ord(c) for c in name) % len(colors)
        return colors[index]

class KanbanColumn:
    def __init__(self, name, is_backlog=False):
        self.name = name
        self.cards = []
        self.is_backlog = is_backlog

class DropPlaceholder(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#3498db', relief='dashed', borderwidth=3, height=80)
        self.pack_propagate(False)
        
        label = tk.Label(self, text="📥 Déposer ici", 
                        font=('Arial', 10, 'bold'), 
                        bg='#3498db', fg='white')
        label.pack(expand=True)

class AvatarWidget(tk.Frame):
    def __init__(self, parent, name, color, size=24):
        super().__init__(parent, bg=parent['bg'])
        
        self.canvas = tk.Canvas(self, width=size, height=size, 
                               bg=parent['bg'], highlightthickness=0)
        self.canvas.pack()
        
        self.canvas.create_oval(2, 2, size-2, size-2, fill=color, outline='white', width=2)
        
        initials = self.get_initials(name)
        self.canvas.create_text(size//2, size//2, text=initials, 
                               fill='white', font=('Arial', int(size*0.4), 'bold'))
    
    def get_initials(self, name):
        if not name:
            return "?"
        
        parts = name.strip().split()
        if len(parts) == 1:
            return parts[0][:2].upper()
        else:
            return (parts[0][0] + parts[-1][0]).upper()

class DragDropCard(tk.Frame):
    def __init__(self, parent, card, app, col_index, card_index):
        super().__init__(parent, bg=card.color, relief='solid', borderwidth=1, 
                        padx=8, pady=6, cursor='hand2', width=220, height=90)
        
        self.card = card
        self.app = app
        self.col_index = col_index
        self.card_index = card_index
        self.dragging = False
        self.drag_window = None
        self.placeholder = None
        
        self.pack_propagate(False)
        self.setup_ui()
        self.setup_drag()
    
    def setup_ui(self):
        header_frame = tk.Frame(self, bg=self.card.color)
        header_frame.pack(fill='x', pady=(0, 3))
        
        title_label = tk.Label(header_frame, text=self.card.title, 
                              font=('Arial', 9, 'bold'), bg=self.card.color,
                              wraplength=180, justify='left')
        title_label.pack(anchor='w', side='left', fill='x', expand=True)
        
        if self.card.assigned_to:
            avatar_frame = tk.Frame(header_frame, bg=self.card.color)
            avatar_frame.pack(side='right')
            
            avatar = AvatarWidget(avatar_frame, self.card.assigned_to, 
                                 self.card.avatar_color, size=20)
            avatar.pack()
        
        if self.card.assigned_to:
            assigned_frame = tk.Frame(self, bg=self.card.color)
            assigned_frame.pack(fill='x', pady=(0, 3))
            
            assigned_label = tk.Label(assigned_frame, text=f"@{self.card.assigned_to}", 
                                    font=('Arial', 8), bg=self.card.color, fg='#2c3e50')
            assigned_label.pack(anchor='w')
        
        if self.card.description:
            desc = self.card.description[:45] + "..." if len(self.card.description) > 45 else self.card.description
            desc_label = tk.Label(self, text=desc, font=('Arial', 7), 
                                bg=self.card.color, fg='#7f8c8d', 
                                wraplength=200, justify='left')
            desc_label.pack(anchor='w', fill='x')
        
        btn_frame = tk.Frame(self, bg=self.card.color)
        btn_frame.pack(fill='x', pady=(3, 0))
        
        edit_btn = tk.Button(btn_frame, text="✏", width=2, height=1,
                           bg='#3498db', fg='white', font=('Arial', 7),
                           command=self.edit, cursor='hand2')
        edit_btn.pack(side='right', padx=1)
        
        delete_btn = tk.Button(btn_frame, text="✗", width=2, height=1,
                             bg='#e74c3c', fg='white', font=('Arial', 7),
                             command=self.delete, cursor='hand2')
        delete_btn.pack(side='right')
    
    def setup_drag(self):
        self.bind('<Button-1>', self.start_drag)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.end_drag)
        
        self.bind_children_drag(self)
    
    def bind_children_drag(self, widget):
        for child in widget.winfo_children():
            if not isinstance(child, tk.Button):
                child.bind('<Button-1>', self.start_drag)
                child.bind('<B1-Motion>', self.on_drag)
                child.bind('<ButtonRelease-1>', self.end_drag)
                self.bind_children_drag(child)
    
    def start_drag(self, event):
        self.dragging = True
        self.start_x = event.x_root
        self.start_y = event.y_root
        
        self.configure(relief='raised', borderwidth=2)
        self.lift()
        
        self.drag_window = tk.Toplevel(self.app.root)
        self.drag_window.wm_overrideredirect(True)
        self.drag_window.configure(bg='#f39c12')
        self.drag_window.attributes('-alpha', 0.8)
        
        drag_frame = tk.Frame(self.drag_window, bg='#f39c12', padx=10, pady=5)
        drag_frame.pack()
        
        tk.Label(drag_frame, text="📋", font=('Arial', 12), bg='#f39c12').pack(side='left')
        tk.Label(drag_frame, text=self.card.title, 
                font=('Arial', 9, 'bold'), bg='#f39c12', fg='white').pack(side='left', padx=(5, 0))
        
        if self.card.assigned_to:
            tk.Label(drag_frame, text=f"@{self.card.assigned_to}", 
                    font=('Arial', 8), bg='#f39c12', fg='#ecf0f1').pack(side='left', padx=(10, 0))
        
        self.drag_window.geometry(f"+{event.x_root+15}+{event.y_root+15}")
        self.drag_window.lift()
    
    def on_drag(self, event):
        if self.dragging and self.drag_window:
            self.drag_window.geometry(f"+{event.x_root+15}+{event.y_root+15}")
            
            self.update_placeholder(event.x_root, event.y_root)
    
    def update_placeholder(self, x, y):
        target_col, insert_index = self.find_drop_position(x, y)
        
        if self.placeholder:
            self.placeholder.destroy()
            self.placeholder = None
        
        for col_frame in self.app.column_frames:
            col_frame.configure(relief='solid', borderwidth=2)
        
        if target_col is not None and target_col != self.col_index:
            target_column = self.app.columns[target_col]
            
            source_col = self.app.columns[self.col_index]
            if not (target_column.is_backlog and not source_col.is_backlog):
                col_frame = self.app.column_frames[target_col]
                col_frame.configure(relief='solid', borderwidth=4, bg='#e8f5e8')
                
                cards_container = self.find_cards_container(col_frame)
                if cards_container:
                    self.placeholder = DropPlaceholder(cards_container)
                    
                    children = [child for child in cards_container.winfo_children() 
                               if isinstance(child, (DragDropCard, DropPlaceholder))]
                    
                    if insert_index < len(children):
                        self.placeholder.pack_forget()
                        self.placeholder.pack(fill='x', pady=3, padx=2, before=children[insert_index])
                    else:
                        self.placeholder.pack(fill='x', pady=3, padx=2)
    
    def find_cards_container(self, col_frame):
        for child in col_frame.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Canvas):
                        for canvas_child in subchild.winfo_children():
                            if isinstance(canvas_child, tk.Frame):
                                return canvas_child
        return None
    
    def find_drop_position(self, x, y):
        for col_index, col_frame in enumerate(self.app.column_frames):
            if not col_frame.winfo_exists():
                continue
                
            col_x = col_frame.winfo_rootx()
            col_y = col_frame.winfo_rooty()
            col_w = col_frame.winfo_width()
            col_h = col_frame.winfo_height()
            
            if col_x <= x <= col_x + col_w and col_y <= y <= col_y + col_h:
                cards_container = self.find_cards_container(col_frame)
                if cards_container:
                    insert_index = 0
                    for child in cards_container.winfo_children():
                        if isinstance(child, DragDropCard) and child != self:
                            child_y = child.winfo_rooty() + child.winfo_height() // 2
                            if y < child_y:
                                break
                            insert_index += 1
                    return col_index, insert_index
                
                return col_index, 0
        
        return None, 0
    
    def end_drag(self, event):
        if not self.dragging:
            return
        
        self.dragging = False
        
        if self.drag_window:
            self.drag_window.destroy()
            self.drag_window = None
        
        if self.placeholder:
            self.placeholder.destroy()
            self.placeholder = None
            
        self.configure(relief='solid', borderwidth=1)
        
        for col_frame in self.app.column_frames:
            col_frame.configure(relief='solid', borderwidth=2)
            column = self.app.columns[self.app.column_frames.index(col_frame)]
            original_bg = '#3498db' if column.is_backlog else '#95a5a6'
            col_frame.configure(bg=original_bg)
        
        target_col, _ = self.find_drop_position(event.x_root, event.y_root)
        
        if target_col is not None and target_col != self.col_index:
            source_col = self.app.columns[self.col_index]
            target_column = self.app.columns[target_col]
            
            if target_column.is_backlog and not source_col.is_backlog:
                messagebox.showwarning("Interdit", "Impossible de déplacer une carte vers le backlog")
                return
            
            self.app.move_card(self.col_index, self.card_index, target_col)
    
    def edit(self):
        self.app.edit_card(self.col_index, self.card_index)
    
    def delete(self):
        self.app.delete_card(self.col_index, self.card_index)

class CardDialog:
    def __init__(self, parent, card=None):
        self.result = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Nouvelle carte" if card is None else "Modifier carte")
        self.window.geometry("480x450")
        self.window.grab_set()
        self.window.resizable(False, False)
        
        self.title_var = tk.StringVar(value=card.title if card else "")
        self.assigned_var = tk.StringVar(value=card.assigned_to if card else "")
        self.color_var = tk.StringVar(value=card.color if card else "#ffffff")
        
        self.assigned_var.trace('w', self.update_avatar_preview)
        
        self.setup_ui()
        self.update_avatar_preview()
        
        if card and card.description:
            self.desc_text.insert('1.0', card.description)
        
        self.center_window()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        tk.Label(main_frame, text="Titre:", font=('Arial', 10, 'bold')).pack(anchor='w')
        title_entry = tk.Entry(main_frame, textvariable=self.title_var, width=50, font=('Arial', 10))
        title_entry.pack(fill='x', pady=(0, 15))
        title_entry.focus()
        
        assigned_frame = tk.Frame(main_frame)
        assigned_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(assigned_frame, text="Assigné à:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        assigned_input_frame = tk.Frame(assigned_frame)
        assigned_input_frame.pack(fill='x', pady=(5, 0))
        
        assigned_entry = tk.Entry(assigned_input_frame, textvariable=self.assigned_var, 
                                 width=40, font=('Arial', 10))
        assigned_entry.pack(side='left', fill='x', expand=True)
        
        self.avatar_preview_frame = tk.Frame(assigned_input_frame, bg='white')
        self.avatar_preview_frame.pack(side='right', padx=(10, 0))
        
        color_frame = tk.Frame(main_frame)
        color_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(color_frame, text="Couleur:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        color_select_frame = tk.Frame(color_frame)
        color_select_frame.pack(fill='x', pady=(5, 0))
        
        self.color_preview = tk.Frame(color_select_frame, bg=self.color_var.get(), 
                                     width=30, height=25, relief='solid', borderwidth=2)
        self.color_preview.pack(side='left', padx=(0, 10))
        
        tk.Button(color_select_frame, text="Choisir", font=('Arial', 9),
                 bg='#3498db', fg='white', command=self.choose_color).pack(side='left')
        
        preset_colors = ['#ffffff', '#ffcccb', '#ffffcc', '#ccffcc', '#ccccff', '#ffccff', '#ffd700']
        for i, color in enumerate(preset_colors):
            btn = tk.Button(color_select_frame, bg=color, width=2, height=1, 
                           relief='solid', borderwidth=1,
                           command=lambda c=color: self.set_color(c))
            btn.pack(side='left', padx=1)
        
        tk.Label(main_frame, text="Description:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        desc_frame = tk.Frame(main_frame)
        desc_frame.pack(fill='both', expand=True, pady=(5, 15))
        
        self.desc_text = tk.Text(desc_frame, height=6, width=50, font=('Arial', 9), wrap='word')
        desc_scroll = tk.Scrollbar(desc_frame, command=self.desc_text.yview)
        self.desc_text.config(yscrollcommand=desc_scroll.set)
        
        self.desc_text.pack(side='left', fill='both', expand=True)
        desc_scroll.pack(side='right', fill='y')
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill='x')
        
        tk.Button(btn_frame, text="Annuler", font=('Arial', 10), 
                 bg='#95a5a6', fg='white', padx=15, pady=5,
                 command=self.cancel).pack(side='right', padx=(10, 0))
        tk.Button(btn_frame, text="OK", font=('Arial', 10, 'bold'), 
                 bg='#27ae60', fg='white', padx=20, pady=5,
                 command=self.ok).pack(side='right')
    
    def update_avatar_preview(self, *args):
        for child in self.avatar_preview_frame.winfo_children():
            child.destroy()
        
        name = self.assigned_var.get().strip()
        if name:
            temp_card = KanbanCard("", assigned_to=name)
            avatar = AvatarWidget(self.avatar_preview_frame, name, temp_card.avatar_color, size=25)
            avatar.pack()
    
    def center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.color_var.get())[1]
        if color:
            self.set_color(color)
    
    def set_color(self, color):
        self.color_var.set(color)
        self.color_preview.config(bg=color)
    
    def ok(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Erreur", "Le titre est obligatoire")
            return
        
        self.result = KanbanCard(
            title=title,
            description=self.desc_text.get('1.0', 'end-1c').strip(),
            assigned_to=self.assigned_var.get().strip(),
            color=self.color_var.get()
        )
        self.window.destroy()
    
    def cancel(self):
        self.window.destroy()

class ResizableActivityPanel:
    def __init__(self, parent, activity_log):
        self.parent = parent
        self.activity_log = activity_log
        
        self.main_frame = tk.Frame(parent)
        self.main_frame.pack(side='right', fill='y')
        
        separator = tk.Frame(self.main_frame, width=4, bg='#bdc3c7', cursor='sb_h_double_arrow')
        separator.pack(side='left', fill='y')
        separator.bind('<Button-1>', self.start_resize)
        separator.bind('<B1-Motion>', self.on_resize)
        
        self.activity_frame = tk.Frame(self.main_frame, bg='#ecf0f1', width=280)
        self.activity_frame.pack(side='right', fill='y')
        self.activity_frame.pack_propagate(False)
        
        header = tk.Frame(self.activity_frame, bg='#34495e', height=50)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="📊 Journal d'activité", 
                font=('Arial', 11, 'bold'), bg='#34495e', fg='white').pack(expand=True)
        
        content_frame = tk.Frame(self.activity_frame, bg='#ecf0f1')
        content_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        self.activity_listbox = tk.Listbox(content_frame, font=('Arial', 8), 
                                          bg='white', selectmode='none')
        activity_scroll = tk.Scrollbar(content_frame, command=self.activity_listbox.yview)
        self.activity_listbox.config(yscrollcommand=activity_scroll.set)
        
        self.activity_listbox.pack(side='left', fill='both', expand=True)
        activity_scroll.pack(side='right', fill='y')
        
        tk.Button(self.activity_frame, text="🔄 Actualiser", 
                 font=('Arial', 8), bg='#3498db', fg='white', relief='flat',
                 command=self.refresh).pack(fill='x', padx=8, pady=(0, 8))
        
        self.refresh()
    
    def start_resize(self, event):
        self.start_x = event.x_root
        self.start_width = self.activity_frame.winfo_width()
    
    def on_resize(self, event):
        dx = self.start_x - event.x_root
        new_width = max(200, min(500, self.start_width + dx))
        self.activity_frame.config(width=new_width)
    
    def add_activity(self, message):
        self.activity_log.add(message)
        self.refresh()
    
    def refresh(self):
        self.activity_listbox.delete(0, tk.END)
        for activity in self.activity_log.activities:
            self.activity_listbox.insert(tk.END, activity)
        if self.activity_log.activities:
            self.activity_listbox.see(0)

class EnhancedKanbanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Enhanced Kanban Board")
        self.root.geometry("1600x900")
        self.root.configure(bg='#ecf0f1')
        
        self.activity_log = ActivityLog()
        self.columns = [
            KanbanColumn("📋 Backlog", is_backlog=True),
            KanbanColumn("📝 À faire"),
            KanbanColumn("⚡ En cours"),
            KanbanColumn("🔍 Révision"),
            KanbanColumn("✅ Terminé")
        ]
        
        self.column_frames = []
        self.setup_ui()
        self.refresh_board()
        
        if os.path.exists("enhanced_kanban.json"):
            self.load_board()
    
    def setup_ui(self):
        main_container = tk.Frame(self.root, bg='#ecf0f1')
        main_container.pack(fill='both', expand=True)
        
        self.activity_panel = ResizableActivityPanel(main_container, self.activity_log)
        
        kanban_frame = tk.Frame(main_container, bg='#ecf0f1')
        kanban_frame.pack(side='left', fill='both', expand=True)
        
        toolbar = tk.Frame(kanban_frame, bg='#2c3e50', height=60)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        toolbar_content = tk.Frame(toolbar, bg='#2c3e50')
        toolbar_content.pack(expand=True, fill='both', padx=20, pady=12)
        
        tk.Label(toolbar_content, text="🚀 Enhanced Kanban", 
                font=('Arial', 14, 'bold'), bg='#2c3e50', fg='white').pack(side='left')
        
        btn_frame = tk.Frame(toolbar_content, bg='#2c3e50')
        btn_frame.pack(side='right')
        
        tk.Button(btn_frame, text="➕ Nouvelle carte", font=('Arial', 9, 'bold'),
                 bg='#27ae60', fg='white', padx=12, pady=6, relief='flat',
                 command=self.add_card_to_backlog).pack(side='left', padx=3)
        
        tk.Button(btn_frame, text="💾 Sauvegarder", font=('Arial', 9, 'bold'),
                 bg='#3498db', fg='white', padx=12, pady=6, relief='flat',
                 command=self.save_board).pack(side='left', padx=3)
        
        tk.Button(btn_frame, text="📁 Charger", font=('Arial', 9, 'bold'),
                 bg='#9b59b6', fg='white', padx=12, pady=6, relief='flat',
                 command=self.load_board).pack(side='left', padx=3)
        
        self.board_frame = tk.Frame(kanban_frame, bg='#ecf0f1')
        self.board_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    def refresh_board(self):
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        
        self.column_frames = []
        
        self.root.update_idletasks()
        available_width = self.board_frame.winfo_width() - 50
        if available_width <= 0:
            available_width = 1200
        
        col_width = max(200, (available_width - (len(self.columns) * 15)) // len(self.columns))
        
        for i, column in enumerate(self.columns):
            self.create_column(column, i, col_width)
    
    def create_column(self, column, col_index, col_width):
        col_frame = tk.Frame(self.board_frame, 
                            bg='#3498db' if column.is_backlog else '#95a5a6', 
                            relief='solid', borderwidth=2, 
                            width=col_width, height=750)
        col_frame.grid(row=0, column=col_index, padx=8, pady=0, sticky='ns')
        col_frame.grid_propagate(False)
        
        self.board_frame.grid_columnconfigure(col_index, weight=1)
        
        self.column_frames.append(col_frame)
        
        header = tk.Frame(col_frame, 
                         bg='#2980b9' if column.is_backlog else '#7f8c8d', 
                         height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title_text = column.name.replace(' ', '\n') if len(column.name) > 10 else column.name
        title_label = tk.Label(header, text=f"{title_text}\n({len(column.cards)})", 
                              font=('Arial', 10, 'bold'), 
                              bg='#2980b9' if column.is_backlog else '#7f8c8d', 
                              fg='white', justify='center')
        title_label.pack(expand=True)
        
        if not column.is_backlog:
            btn_frame = tk.Frame(header, bg='#7f8c8d')
            btn_frame.pack(side='bottom', fill='x')
            
            if col_index > 1:
                left_btn = tk.Button(btn_frame, text="◀", width=3, height=1,
                                   bg='white', font=('Arial', 7),
                                   command=lambda: self.move_column_left(col_index))
                left_btn.pack(side='left', padx=1)
            
            if col_index < len(self.columns) - 1:
                right_btn = tk.Button(btn_frame, text="▶", width=3, height=1,
                                    bg='white', font=('Arial', 7),
                                    command=lambda: self.move_column_right(col_index))
                right_btn.pack(side='left', padx=1)
        
        cards_container_frame = tk.Frame(col_frame, bg='white')
        cards_container_frame.pack(fill='both', expand=True, padx=3, pady=3)
        
        cards_canvas = tk.Canvas(cards_container_frame, bg='white', highlightthickness=0)
        cards_scroll = tk.Scrollbar(cards_container_frame, orient='vertical', 
                                   command=cards_canvas.yview, width=12)
        cards_canvas.configure(yscrollcommand=cards_scroll.set)
        
        cards_canvas.pack(side='left', fill='both', expand=True)
        cards_scroll.pack(side='right', fill='y')
        
        cards_frame = tk.Frame(cards_canvas, bg='white')
        cards_canvas.create_window((0, 0), window=cards_frame, anchor='nw')
        
        for card_index, card in enumerate(column.cards):
            card_widget = DragDropCard(cards_frame, card, self, col_index, card_index)
            card_widget.pack(fill='x', pady=4, padx=3)
        
        if column.is_backlog:
            add_btn = tk.Button(cards_frame, text="➕ Nouvelle carte", 
                               font=('Arial', 9, 'bold'),
                               bg='#27ae60', fg='white', pady=6, relief='flat',
                               command=self.add_card_to_backlog)
            add_btn.pack(fill='x', pady=8, padx=5)
        
        def configure_scroll(event):
            cards_canvas.configure(scrollregion=cards_canvas.bbox("all"))
        
        cards_frame.bind('<Configure>', configure_scroll)
        cards_canvas.bind('<MouseWheel>', lambda e: cards_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        def configure_canvas_width(event):
            canvas_width = event.width
            cards_canvas.itemconfig(cards_canvas.winfo_children()[0], width=canvas_width)
        
        cards_canvas.bind('<Configure>', configure_canvas_width)
    
    def move_column_left(self, col_index):
        if col_index > 1:
            self.columns[col_index], self.columns[col_index-1] = \
                self.columns[col_index-1], self.columns[col_index]
            self.activity_panel.add_activity(f"Colonne '{self.columns[col_index-1].name}' déplacée ←")
            self.refresh_board()
    
    def move_column_right(self, col_index):
        if col_index < len(self.columns) - 1:
            self.columns[col_index], self.columns[col_index+1] = \
                self.columns[col_index+1], self.columns[col_index]
            self.activity_panel.add_activity(f"Colonne '{self.columns[col_index+1].name}' déplacée →")
            self.refresh_board()
    
    def add_card_to_backlog(self):
        backlog_col = None
        for col in self.columns:
            if col.is_backlog:
                backlog_col = col
                break
        
        if not backlog_col:
            messagebox.showerror("Erreur", "Pas de backlog trouvé")
            return
        
        dialog = CardDialog(self.root)
        self.root.wait_window(dialog.window)
        
        if dialog.result:
            backlog_col.cards.append(dialog.result)
            assigned_text = f" → @{dialog.result.assigned_to}" if dialog.result.assigned_to else ""
            self.activity_panel.add_activity(f"✨ Nouvelle carte '{dialog.result.title}'{assigned_text}")
            self.refresh_board()
    
    def edit_card(self, col_index, card_index):
        card = self.columns[col_index].cards[card_index]
        old_title = card.title
        old_assigned = card.assigned_to
        
        dialog = CardDialog(self.root, card)
        self.root.wait_window(dialog.window)
        
        if dialog.result:
            self.columns[col_index].cards[card_index] = dialog.result
            changes = []
            if old_title != dialog.result.title:
                changes.append(f"titre: '{dialog.result.title}'")
            if old_assigned != dialog.result.assigned_to:
                changes.append(f"assigné: @{dialog.result.assigned_to}")
            
            change_text = " (" + ", ".join(changes) + ")" if changes else ""
            self.activity_panel.add_activity(f"✏ Carte modifiée{change_text}")
            self.refresh_board()
    
    def delete_card(self, col_index, card_index):
        card = self.columns[col_index].cards[card_index]
        if messagebox.askyesno("Confirmer", f"Supprimer '{card.title}' ?"):
            self.columns[col_index].cards.pop(card_index)
            self.activity_panel.add_activity(f"🗑 Carte '{card.title}' supprimée")
            self.refresh_board()
    
    def move_card(self, from_col, card_index, to_col):
        card = self.columns[from_col].cards.pop(card_index)
        self.columns[to_col].cards.append(card)
        
        from_name = self.columns[from_col].name
        to_name = self.columns[to_col].name
        assigned_text = f" (@{card.assigned_to})" if card.assigned_to else ""
        
        self.activity_panel.add_activity(f"🔄 '{card.title}': {from_name} → {to_name}{assigned_text}")
        self.refresh_board()
    
    def save_board(self):
        try:
            data = {
                'columns': [],
                'activities': self.activity_log.activities,
                'saved_at': datetime.now().isoformat()
            }
            
            for col in self.columns:
                col_data = {
                    'name': col.name,
                    'is_backlog': col.is_backlog,
                    'cards': []
                }
                for card in col.cards:
                    card_data = {
                        'title': card.title,
                        'description': card.description,
                        'assigned_to': card.assigned_to,
                        'color': card.color,
                        'id': card.id
                    }
                    col_data['cards'].append(card_data)
                data['columns'].append(col_data)
            
            with open("enhanced_kanban.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.activity_panel.add_activity("💾 Tableau sauvegardé")
            messagebox.showinfo("Succès", "Tableau sauvegardé avec succès !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de sauvegarde:\n{str(e)}")
    
    def load_board(self):
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            initialfile="enhanced_kanban.json",
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.columns = []
            for col_data in data.get('columns', []):
                column = KanbanColumn(col_data['name'], col_data.get('is_backlog', False))
                for card_data in col_data.get('cards', []):
                    card = KanbanCard(
                        title=card_data['title'],
                        description=card_data.get('description', ''),
                        assigned_to=card_data.get('assigned_to', ''),
                        color=card_data.get('color', '#ffffff')
                    )
                    card.id = card_data.get('id', card.id)
                    column.cards.append(card)
                self.columns.append(column)
            
            if 'activities' in data:
                self.activity_log.activities = data['activities']
                self.activity_panel.refresh()
            
            self.activity_panel.add_activity(f"📁 Tableau chargé: {os.path.basename(filename)}")
            self.refresh_board()
            messagebox.showinfo("Succès", f"Tableau chargé: {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de chargement:\n{str(e)}")

def main():
    root = tk.Tk()
    app = EnhancedKanbanApp(root)
    
    def on_closing():
        if messagebox.askyesno("Quitter", "💾 Sauvegarder avant de quitter ?"):
            app.save_board()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.bind('<Control-s>', lambda e: app.save_board())
    root.bind('<Control-o>', lambda e: app.load_board())
    root.bind('<Control-n>', lambda e: app.add_card_to_backlog())
    
    root.bind('<Configure>', lambda e: app.refresh_board() if e.widget == root else None)
    
    root.focus_force()
    root.mainloop()

if __name__ == "__main__":
    main()

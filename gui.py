import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from datetime import datetime
import os
import pandas as pd
import json
from main import RemoteJobScraper
from config import KEYWORDS

class JobDetailsWindow:
    def __init__(self, parent, job_data):
        self.window = tk.Toplevel(parent)
        self.window.title("Job Details")
        self.window.geometry("600x400")
        
        # Create scrolled text widget
        self.text = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, width=70, height=20)
        self.text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Insert job details
        for key, value in job_data.items():
            self.text.insert(tk.END, f"{key.title()}: {value}\n")
        
        self.text.configure(state='disabled')

class JobScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Remote Job Scraper")
        self.root.geometry("1000x800")
        
        # Create main container with padding
        self.main_container = ttk.Frame(root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        self.setup_gui()
        self.scraper = None
        self.is_scraping = False
        self.all_jobs_data = {}
        
    def setup_gui(self):
        # Keyword management section
        keyword_frame = ttk.LabelFrame(self.main_container, text="Job Keywords", padding="5")
        keyword_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Existing keywords
        self.keyword_vars = {}
        keyword_scroll = ttk.Frame(keyword_frame)
        keyword_scroll.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        for i, keyword in enumerate(KEYWORDS):
            var = tk.BooleanVar(value=True)
            self.keyword_vars[keyword] = var
            ttk.Checkbutton(keyword_scroll, text=keyword, variable=var).grid(
                row=i//3, column=i%3, sticky=tk.W, padx=5
            )
        
        # Custom keyword entry
        custom_frame = ttk.Frame(keyword_frame)
        custom_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.custom_keyword = ttk.Entry(custom_frame)
        self.custom_keyword.grid(row=0, column=0, padx=5)
        
        ttk.Button(custom_frame, text="Add Keyword", command=self.add_custom_keyword).grid(
            row=0, column=1, padx=5
        )
        
        # Control buttons
        button_frame = ttk.Frame(self.main_container)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Export buttons
        export_frame = ttk.Frame(button_frame)
        export_frame.grid(row=0, column=2, padx=20)
        
        ttk.Button(export_frame, text="Export CSV", command=lambda: self.export_results('csv')).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(export_frame, text="Export JSON", command=lambda: self.export_results('json')).grid(
            row=0, column=1, padx=5
        )
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.main_container, text="Progress", padding="5")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_var = tk.StringVar(value="Ready to start...")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Log section
        log_frame = ttk.LabelFrame(self.main_container, text="Log", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Results section with filtering
        results_frame = ttk.LabelFrame(self.main_container, text="Latest Results", padding="5")
        results_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Filter frame
        filter_frame = ttk.Frame(results_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(filter_frame, text="Filter:").grid(row=0, column=0, padx=5)
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', self.apply_filter)
        ttk.Entry(filter_frame, textvariable=self.filter_var).grid(row=0, column=1, padx=5)
        
        # Results tree
        self.results_tree = ttk.Treeview(
            results_frame, 
            columns=('Keyword', 'Jobs Found', 'Last Updated', 'Source'),
            show='headings',
            height=10
        )
        self.results_tree.heading('Keyword', text='Keyword', command=lambda: self.treeview_sort_column('Keyword'))
        self.results_tree.heading('Jobs Found', text='Jobs Found', command=lambda: self.treeview_sort_column('Jobs Found'))
        self.results_tree.heading('Last Updated', text='Last Updated', command=lambda: self.treeview_sort_column('Last Updated'))
        self.results_tree.heading('Source', text='Source', command=lambda: self.treeview_sort_column('Source'))
        self.results_tree.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Double click to view details
        self.results_tree.bind('<Double-1>', self.show_job_details)
        
        # Configure scrollbar for results
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Make the main container expandable
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(3, weight=1)
        
    def add_custom_keyword(self):
        keyword = self.custom_keyword.get().strip().lower().replace(' ', '-')
        if keyword and keyword not in self.keyword_vars:
            var = tk.BooleanVar(value=True)
            self.keyword_vars[keyword] = var
            ttk.Checkbutton(self.main_container, text=keyword, variable=var).grid(
                row=len(self.keyword_vars)//3, column=len(self.keyword_vars)%3, sticky=tk.W, padx=5
            )
            self.custom_keyword.delete(0, tk.END)
            
    def show_job_details(self, event):
        item = self.results_tree.selection()[0]
        keyword = self.results_tree.item(item)['values'][0]
        if keyword in self.all_jobs_data:
            JobDetailsWindow(self.root, self.all_jobs_data[keyword])
            
    def treeview_sort_column(self, col):
        l = [(self.results_tree.set(k, col), k) for k in self.results_tree.get_children('')]
        l.sort(reverse=self.results_tree.heading(col).get('reverse', False))
        
        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.results_tree.move(k, '', index)
            
        # Reverse sort next time
        self.results_tree.heading(col, reverse=not self.results_tree.heading(col).get('reverse', False))
        
    def apply_filter(self, *args):
        filter_text = self.filter_var.get().lower()
        self.update_results_tree(filter_text)
        
    def export_results(self, format_type):
        if not self.all_jobs_data:
            messagebox.showwarning("Warning", "No data to export")
            return
            
        file_types = {
            'csv': [('CSV files', '*.csv')],
            'json': [('JSON files', '*.json')]
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=file_types[format_type]
        )
        
        if filename:
            if format_type == 'csv':
                pd.DataFrame(self.all_jobs_data).to_csv(filename, index=False)
            else:
                with open(filename, 'w') as f:
                    json.dump(self.all_jobs_data, f, indent=2)
            messagebox.showinfo("Success", f"Data exported to {filename}")
        
    def show_completion_summary(self):
        total_jobs = sum(len(jobs) for jobs in self.all_jobs_data.values())
        summary = f"Scraping Completed!\n\n"
        summary += f"Total Jobs Found: {total_jobs}\n\n"
        summary += "Summary by Keyword:\n"
        
        for keyword, jobs in self.all_jobs_data.items():
            summary += f"- {keyword}: {len(jobs)} jobs\n"
        
        messagebox.showinfo("Scraping Complete", summary)
        
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def update_progress(self, current, total):
        progress = (current / total) * 100
        self.progress_bar['value'] = progress
        self.progress_var.set(f"Processing {current}/{total} keywords...")
        
    def update_results_tree(self, filter_text=None):
        self.results_tree.delete(*self.results_tree.get_children())
        for keyword in self.keyword_vars:
            if self.keyword_vars[keyword].get():
                csv_path = os.path.join('output', keyword, f'{keyword}_jobs.csv')
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    job_count = len(df)
                    last_updated = df['last_updated'].max() if 'last_updated' in df.columns else 'N/A'
                    source = df['source'].unique()[0] if 'source' in df.columns else 'N/A'
                    if filter_text is None or keyword.lower().find(filter_text) != -1:
                        self.results_tree.insert('', 'end', values=(keyword, job_count, last_updated, source))
        
    def start_scraping(self):
        if self.is_scraping:
            return
            
        selected_keywords = [k for k, v in self.keyword_vars.items() if v.get()]
        if not selected_keywords:
            messagebox.showwarning("Warning", "Please select at least one keyword")
            return
            
        self.is_scraping = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar['value'] = 0
        
        # Start scraping in a separate thread
        thread = threading.Thread(target=self.scrape_jobs, args=(selected_keywords,))
        thread.daemon = True
        thread.start()
        
    def stop_scraping(self):
        self.is_scraping = False
        self.log("Stopping scraper...")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
    def scrape_jobs(self, keywords):
        self.scraper = RemoteJobScraper()
        total_keywords = len(keywords)
        self.all_jobs_data = {}
        
        try:
            for i, keyword in enumerate(keywords, 1):
                if not self.is_scraping:
                    break
                    
                self.log(f"Searching for {keyword} jobs...")
                self.scraper.search_remote_jobs(keyword)
                self.scraper.save_results(keyword)
                
                # Store jobs data for this keyword
                csv_path = os.path.join('output', keyword, f'{keyword}_jobs.csv')
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    self.all_jobs_data[keyword] = df.to_dict('records')
                
                self.update_progress(i, total_keywords)
                self.update_results_tree()
                
            self.log("Job search completed!")
            if self.is_scraping:  # Only show summary if not stopped manually
                self.root.after(100, self.show_completion_summary)
            
        except Exception as e:
            self.log(f"Error during scraping: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during scraping: {str(e)}")
            
        finally:
            if self.scraper:
                self.scraper.close()
            self.is_scraping = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.progress_var.set("Ready to start...")
        
def main():
    root = tk.Tk()
    app = JobScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

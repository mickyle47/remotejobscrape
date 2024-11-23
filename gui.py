import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from datetime import datetime
import os
import pandas as pd
import json
from main import RemoteJobScraper
from logging_config import logger
import config  # Import config module directly

class JobScraperGUI:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("Remote Job Scraper")
            self.is_scraping = False
            self.all_jobs_data = []
            
            # Configure grid weights to make it responsive
            self.root.grid_rowconfigure(1, weight=1)  # Results row expands
            self.root.grid_columnconfigure(0, weight=1)  # Main column expands
            
            # Create main container frame
            self.main_frame = ttk.Frame(self.root)
            self.main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=5)
            self.main_frame.grid_columnconfigure(0, weight=1)
            
            # Create and pack the top section (keywords)
            self.create_keyword_section()
            
            # Create results section in a separate frame
            self.results_frame = ttk.Frame(self.root)
            self.results_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
            self.results_frame.grid_columnconfigure(0, weight=1)
            self.results_frame.grid_rowconfigure(0, weight=1)
            
            # Create results tree with scrollbar
            self.create_results_tree()
            
            # Create bottom section
            self.create_bottom_section()
            
            # Log successful initialization
            self.log("GUI initialized successfully")
            
        except Exception as e:
            # Log any initialization errors
            error_msg = f"Error initializing GUI: {str(e)}"
            if hasattr(self, 'log'):
                self.log(error_msg)
            else:
                # If log widget isn't created yet, use logger directly
                from logging_config import logger
                logger.error(error_msg, exc_info=True)
            raise  # Re-raise the exception after logging
            
    def create_keyword_section(self):
        # Keywords section
        keywords_frame = ttk.LabelFrame(self.main_frame, text="Keywords", padding="5")
        keywords_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Select/Unselect All buttons
        select_buttons_frame = ttk.Frame(keywords_frame)
        select_buttons_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(select_buttons_frame, text="Select All", command=lambda: self.toggle_all_keywords(True)).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(select_buttons_frame, text="Unselect All", command=lambda: self.toggle_all_keywords(False)).grid(
            row=0, column=1, padx=5
        )
        
        # Create checkboxes for predefined keywords
        self.keyword_vars = {}
        for i, keyword in enumerate(config.KEYWORDS):
            var = tk.BooleanVar(value=True)
            self.keyword_vars[keyword] = var
            ttk.Checkbutton(
                keywords_frame,
                text=keyword,
                variable=var
            ).grid(row=i//3 + 1, column=i%3, sticky=tk.W, padx=5)
        
        # Custom keyword entry - moved below keywords
        custom_frame = ttk.Frame(self.main_frame)
        custom_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.custom_keyword = ttk.Entry(custom_frame)
        self.custom_keyword.grid(row=0, column=0, padx=5)
        
        ttk.Button(custom_frame, text="Add Keyword", command=self.add_custom_keyword).grid(
            row=0, column=1, padx=5
        )
        
        # Control buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, pady=5, padx=5)
        
        self.start_button = ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Export buttons
        ttk.Button(button_frame, text="Export CSV", command=lambda: self.export_results('csv')).grid(
            row=0, column=2, padx=5
        )
        ttk.Button(button_frame, text="Export JSON", command=lambda: self.export_results('json')).grid(
            row=0, column=3, padx=5
        )
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.main_frame, text="Progress", padding="5")
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.progress_var = tk.StringVar(value="Ready to start...")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
    def create_results_tree(self):
        """Create the results treeview with scrollbars"""
        # Create frame for treeview and scrollbars
        tree_frame = ttk.Frame(self.results_frame)
        tree_frame.grid(row=0, column=0, sticky='nsew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Create vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.grid(row=0, column=1, sticky='ns')
        
        # Create horizontal scrollbar
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.grid(row=1, column=0, sticky='ew')
        
        # Create treeview
        self.results_tree = ttk.Treeview(tree_frame, selectmode='browse', 
                                        yscrollcommand=vsb.set,
                                        xscrollcommand=hsb.set)
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        
        # Configure scrollbars
        vsb.config(command=self.results_tree.yview)
        hsb.config(command=self.results_tree.xview)
        
        # Configure columns
        self.results_tree["columns"] = ("Company", "Date", "Source", "Link")
        self.results_tree.column("#0", width=300, minwidth=200)  # Title column
        self.results_tree.column("Company", width=150, minwidth=100)
        self.results_tree.column("Date", width=100, minwidth=100)
        self.results_tree.column("Source", width=100, minwidth=100)
        self.results_tree.column("Link", width=300, minwidth=200)
        
        # Configure column headings
        self.results_tree.heading("#0", text="Job Title", anchor=tk.W)
        self.results_tree.heading("Company", text="Company", anchor=tk.W)
        self.results_tree.heading("Date", text="Date Posted", anchor=tk.W)
        self.results_tree.heading("Source", text="Source", anchor=tk.W)
        self.results_tree.heading("Link", text="URL", anchor=tk.W)
        
        # Configure tags for URL styling
        self.results_tree.tag_configure('link', foreground='blue')
        
        # Bind double-click event
        self.results_tree.bind('<Double-1>', self.on_tree_double_click)
        self.results_tree.bind('<Button-1>', self.on_tree_click)
        
    def create_bottom_section(self):
        # Log section - moved below results
        log_frame = ttk.LabelFrame(self.root, text="Log", padding="5")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.S), padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=3)  # Results get more space
        self.root.grid_rowconfigure(2, weight=1)  # Log gets less space
        self.root.grid_columnconfigure(0, weight=1)
        
    def add_custom_keyword(self):
        keyword = self.custom_keyword.get().strip().lower().replace(' ', '-')
        if keyword and keyword not in self.keyword_vars:
            var = tk.BooleanVar(value=True)
            self.keyword_vars[keyword] = var
            ttk.Checkbutton(self.main_frame, text=keyword, variable=var).grid(
                row=len(self.keyword_vars)//3 + 4, column=len(self.keyword_vars)%3, sticky=tk.W, padx=5
            )
            self.custom_keyword.delete(0, tk.END)
            
    def show_job_details(self, event):
        item = self.results_tree.selection()[0]
        job_title = self.results_tree.item(item)['text']
        for job in self.all_jobs_data:
            if job['title'] == job_title:
                JobDetailsWindow(self.root, job)
                break
            
    def apply_filter(self, *args):
        filter_text = self.filter_var.get().lower()
        self.update_results_tree(filter_text)
        
    def export_results(self, format_type):
        """Export results to CSV or JSON file"""
        if not self.all_jobs_data:
            messagebox.showwarning("No Data", "No job data available to export!")
            return
            
        # Create a list of dictionaries for DataFrame
        jobs_list = []
        for job in self.all_jobs_data:
            job_dict = {
                'Title': job.get('title', ''),
                'Company': job.get('company', ''),
                'Location': job.get('location', 'Remote'),
                'Source': job.get('source', ''),
                'URL': job.get('url', ''),
                'Date Posted': job.get('date_posted', ''),
                'Keyword': job.get('keyword', '')
            }
            jobs_list.append(job_dict)
            
        # Get file name from user
        if format_type == 'csv':
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Export as CSV"
            )
        else:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Export as JSON"
            )
            
        if filename:
            try:
                if format_type == 'csv':
                    df = pd.DataFrame(jobs_list)
                    df.to_csv(filename, index=False, encoding='utf-8')
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(jobs_list, f, indent=2, ensure_ascii=False)
                        
                messagebox.showinfo("Success", f"Data exported successfully to {filename}")
                
                # Open the containing folder
                folder_path = os.path.dirname(os.path.abspath(filename))
                os.startfile(folder_path)
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting data: {str(e)}")
        
    def show_completion_summary(self):
        """Show summary of scraped jobs"""
        if not self.all_jobs_data:
            messagebox.showinfo("Scraping Complete", "No jobs found.")
            return
            
        # Group jobs by keyword
        keyword_jobs = {}
        for job in self.all_jobs_data:
            keyword = job['keyword']
            if keyword not in keyword_jobs:
                keyword_jobs[keyword] = []
            keyword_jobs[keyword].append(job)
        
        # Create summary
        total_jobs = len(self.all_jobs_data)
        summary = f"Scraping Completed!\n\n"
        summary += f"Total Jobs Found: {total_jobs}\n\n"
        summary += "Summary by Keyword:\n"
        
        for keyword, jobs in keyword_jobs.items():
            sources = set(job.get('source', '') for job in jobs)
            summary += f"- {keyword}: {len(jobs)} jobs from {', '.join(sources)}\n"
        
        messagebox.showinfo("Scraping Complete", summary)
        
    def start_scraping(self):
        """Start the scraping process"""
        if self.is_scraping:
            return
        
        selected_keywords = [
            keyword for keyword, var in self.keyword_vars.items()
            if var.get()
        ]
        
        if not selected_keywords:
            messagebox.showwarning(
                "No Keywords",
                "Please select at least one keyword to search for."
            )
            return
            
        self.progress_var.set("Starting scraper...")
        self.is_scraping = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Clear previous results
        self.all_jobs_data = []
        self.results_tree.delete(*self.results_tree.get_children())
        
        def scrape():
            try:
                self.scraper = RemoteJobScraper()
                total_keywords = len(selected_keywords)
                
                for idx, keyword in enumerate(selected_keywords, 1):
                    if not self.is_scraping:
                        break
                        
                    self.progress_var.set(f"Searching for {keyword} jobs... ({idx}/{total_keywords})")
                    self.log(f"Searching for {keyword} jobs...")
                    
                    # Get jobs for this keyword
                    jobs = self.scraper.scrape_jobs([keyword])
                    
                    # Add jobs to the list with keyword
                    for job in jobs:
                        job['keyword'] = keyword
                        self.all_jobs_data.append(job)
                        self.log(f"Found job: {job['title']} at {job['company']}")
                    
                    # Update progress
                    progress = (idx / total_keywords) * 100
                    self.progress_bar['value'] = progress
                    
                    # Update the results tree after each keyword
                    self.root.after(0, self.update_results_tree)
                    
                if self.is_scraping:
                    self.progress_var.set("Scraping completed!")
                    self.log(f"Found {len(self.all_jobs_data)} total jobs")
                    self.root.after(0, self.show_completion_summary)
                
            except Exception as e:
                logger.error(f"Error during scraping: {str(e)}")
                self.progress_var.set(f"Error: {str(e)}")
                self.log(f"Error during scraping: {str(e)}")
                messagebox.showerror("Error", f"An error occurred during scraping: {str(e)}")
            finally:
                self.is_scraping = False
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                if hasattr(self, 'scraper'):
                    self.scraper.close()
                    
        # Start scraping in a separate thread
        thread = threading.Thread(target=scrape)
        thread.daemon = True
        thread.start()
        
    def update_results_tree(self, filter_text=''):
        """Update the results tree with job data"""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Filter and insert jobs
        for job in self.all_jobs_data:
            # Apply filter if any
            if filter_text.lower() not in str(job).lower():
                continue
                    
            # Insert job into tree
            values = (
                job.get('company', ''),
                job.get('date_posted', ''),  # Use date_posted instead of date
                job.get('source', ''),
                job.get('url', '')
            )
            
            item = self.results_tree.insert('', 'end', text=job.get('title', ''), values=values, tags=('link',))
            
            # Apply direct job tag if applicable
            if job.get('is_company_direct', False):
                current_tags = list(self.results_tree.item(item, 'tags'))
                current_tags.append('direct_job')
                self.results_tree.item(item, tags=current_tags)
        
    def stop_scraping(self):
        self.is_scraping = False
        self.log("Stopping scraper...")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
    def toggle_all_keywords(self, state):
        """Toggle all keyword checkboxes to specified state"""
        for var in self.keyword_vars.values():
            var.set(state)
            
    def log(self, message):
        """Add message to log text widget"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def on_tree_click(self, event):
        """Handle single click on tree item"""
        region = self.results_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.results_tree.identify_column(event.x)
            item = self.results_tree.identify_row(event.y)
            if item:
                # Change cursor to hand when over link
                self.results_tree.config(cursor="hand2")
                return
        self.results_tree.config(cursor="")
        
    def on_tree_double_click(self, event):
        """Handle double click on tree item"""
        region = self.results_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.results_tree.identify_column(event.x)
            item = self.results_tree.identify_row(event.y)
            if item:
                # Get the URL from the Link column
                url = self.results_tree.item(item)['values'][3]
                if url:
                    import webbrowser
                    webbrowser.open(url)
        
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

def main():
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists('output'):
            os.makedirs('output')
        
        root = tk.Tk()
        app = JobScraperGUI(root)
        root.mainloop()
    except Exception as e:
        # Log any main function errors
        from logging_config import logger
        logger.error(f"Error in main function: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

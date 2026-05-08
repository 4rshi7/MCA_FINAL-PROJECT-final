import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# ====== CONFIG ======
CLIP_PATH = "Abuse001_x264.npy"  # Change path if needed
SAVE_DIR = "Clip_Visualizations2"
os.makedirs(SAVE_DIR, exist_ok=True)

# ====== LOAD CLIP ======
features = np.load(CLIP_PATH)  # (192, 16, 10, 10)
print("Loaded clip features:", features.shape)

# Grid configuration
rows, cols = 12, 16  # 16*12 = 192
cell_size = 36

class FeatureVisualizer:
    def __init__(self, features):
        self.features = features
        self.current_t = 0
        self.max_t = features.shape[1] - 1  # 15 (0-15)
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(15, 12))
        self.fig.suptitle('X3D Features Visualizer - Navigate through time steps', fontsize=16)
        
        # Create buttons
        self.create_buttons()
        
        # Initial visualization
        self.update_visualization()
        
        plt.tight_layout()
        plt.show()
    
    def create_buttons(self):
        # Button positions [left, bottom, width, height]
        ax_prev = plt.axes([0.1, 0.02, 0.1, 0.05])
        ax_next = plt.axes([0.25, 0.02, 0.1, 0.05])
        ax_first = plt.axes([0.4, 0.02, 0.1, 0.05])
        ax_last = plt.axes([0.55, 0.02, 0.1, 0.05])
        ax_save = plt.axes([0.7, 0.02, 0.1, 0.05])
        ax_save_all = plt.axes([0.85, 0.02, 0.1, 0.05])
        
        self.btn_prev = Button(ax_prev, 'Previous')
        self.btn_next = Button(ax_next, 'Next')
        self.btn_first = Button(ax_first, 'First')
        self.btn_last = Button(ax_last, 'Last')
        self.btn_save = Button(ax_save, 'Save')
        self.btn_save_all = Button(ax_save_all, 'Save All')
        
        # Connect button events
        self.btn_prev.on_clicked(self.prev_frame)
        self.btn_next.on_clicked(self.next_frame)
        self.btn_first.on_clicked(self.first_frame)
        self.btn_last.on_clicked(self.last_frame)
        self.btn_save.on_clicked(self.save_current)
        self.btn_save_all.on_clicked(self.save_all)
    
    def normalize_channel(self, ch):
        """Normalize a single channel to 0-255 range"""
        ch = ch - ch.min()
        if ch.max() > 0:
            ch = ch / ch.max()
        return (ch * 255).astype(np.uint8)
    
    def create_grid_visualization(self, t):
        """Create grid visualization for time step t"""
        slice_t = self.features[:, t, :, :]  # (192, 10, 10)
        grid_img = np.zeros((rows * cell_size, cols * cell_size), dtype=np.uint8)
        
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx < slice_t.shape[0]:
                    ch = self.normalize_channel(slice_t[idx])
                    ch_resized = cv2.resize(ch, (cell_size, cell_size), interpolation=cv2.INTER_CUBIC)
                    grid_img[r * cell_size:(r + 1) * cell_size,
                             c * cell_size:(c + 1) * cell_size] = ch_resized
                idx += 1
        
        return grid_img
    
    def update_visualization(self):
        """Update the visualization with current time step"""
        self.ax.clear()
        
        grid_img = self.create_grid_visualization(self.current_t)
        
        # Display as grayscale
        self.ax.imshow(grid_img, cmap='gray', vmin=0, vmax=255)
        self.ax.set_title(f'Time Step: {self.current_t}/{self.max_t} | Shape: (192, 10, 10)', 
                         fontsize=14, pad=20)
        self.ax.axis('off')
        
        # Add grid lines to separate channels
        for r in range(1, rows):
            self.ax.axhline(y=r * cell_size - 0.5, color='red', linewidth=0.5, alpha=0.3)
        for c in range(1, cols):
            self.ax.axvline(x=c * cell_size - 0.5, color='red', linewidth=0.5, alpha=0.3)
        
        # Add channel numbers (optional - can be commented out if too cluttered)
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if idx < 192:
                    text_x = c * cell_size + cell_size // 2
                    text_y = r * cell_size + 5
                    self.ax.text(text_x, text_y, str(idx), fontsize=8, ha='center', 
                               color='white', weight='bold', alpha=0.7)
        
        self.fig.canvas.draw()
    
    def prev_frame(self, event):
        if self.current_t > 0:
            self.current_t -= 1
            self.update_visualization()
    
    def next_frame(self, event):
        if self.current_t < self.max_t:
            self.current_t += 1
            self.update_visualization()
    
    def first_frame(self, event):
        self.current_t = 0
        self.update_visualization()
    
    def last_frame(self, event):
        self.current_t = self.max_t
        self.update_visualization()
    
    def save_current(self, event):
        """Save current visualization"""
        grid_img = self.create_grid_visualization(self.current_t)
        output_path = os.path.join(SAVE_DIR, f"clip1_t{self.current_t:02d}.png")
        cv2.imwrite(output_path, grid_img)
        print(f"Saved: {output_path}")
    
    def save_all(self, event):
        """Save all time steps"""
        print("Saving all time steps...")
        for t in range(self.features.shape[1]):
            grid_img = self.create_grid_visualization(t)
            output_path = os.path.join(SAVE_DIR, f"clip1_t{t:02d}.png")
            cv2.imwrite(output_path, grid_img)
        print(f"Saved all {self.features.shape[1]} time steps to {SAVE_DIR}/")

# ====== ALTERNATIVE: Simple Navigation Function ======
def simple_navigator():
    """Simple function-based navigator without class"""
    features = np.load(CLIP_PATH)
    current_t = 0
    
    def show_timestep(t):
        slice_t = features[:, t, :, :]  # (192, 10, 10)
        grid_img = np.zeros((rows * cell_size, cols * cell_size), dtype=np.uint8)
        
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx < slice_t.shape[0]:
                    ch = slice_t[idx]
                    ch = ch - ch.min()
                    if ch.max() > 0:
                        ch = ch / ch.max()
                    ch = (ch * 255).astype(np.uint8)
                    ch_resized = cv2.resize(ch, (cell_size, cell_size), interpolation=cv2.INTER_CUBIC)
                    grid_img[r * cell_size:(r + 1) * cell_size,
                             c * cell_size:(c + 1) * cell_size] = ch_resized
                idx += 1
        
        plt.figure(figsize=(15, 12))
        plt.imshow(grid_img, cmap='gray', vmin=0, vmax=255)
        plt.title(f'X3D Features - Time Step: {t}/15 | Shape: (192, 10, 10)', fontsize=16)
        plt.axis('off')
        
        # Add grid lines
        for r in range(1, rows):
            plt.axhline(y=r * cell_size - 0.5, color='red', linewidth=0.5, alpha=0.3)
        for c in range(1, cols):
            plt.axvline(x=c * cell_size - 0.5, color='red', linewidth=0.5, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Save option
        output_path = os.path.join(SAVE_DIR, f"clip1_t{t:02d}.png")
        cv2.imwrite(output_path, grid_img)
        print(f"Saved: {output_path}")
    
    return show_timestep

# ====== USAGE ======
print("Choose visualization method:")
print("1. Interactive navigator with buttons:")
print("   visualizer = FeatureVisualizer(features)")
print("\n2. Simple function calls:")
print("   show_func = simple_navigator()")
print("   show_func(0)  # Show time step 0")
print("   show_func(5)  # Show time step 5")
print("   # etc.")

# Uncomment one of these to start:
# Interactive version
visualizer = FeatureVisualizer(features)

# Or simple version
# show_func = simple_navigator()
# show_func(0)  # Show first time step
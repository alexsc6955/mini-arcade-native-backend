#pragma once

#include <SDL.h>
#include <SDL_ttf.h>
#include <vector>

// A minimal 2D graphics engine binding for Python using SDL.
namespace mini {

    // We define our own event types so Python doesn't need to know about SDL constants.
    enum class EventType {
        Unknown = 0,
        Quit,
        KeyDown,
        KeyUp
    };

    // A simple event structure to pass events to Python.
    struct Event {
        EventType type;
        int key;  // SDL key code (e.g., 27 for ESC). 0 if not applicable.
    };

    // The main engine class that wraps SDL functionality.
    class Engine {
    public:
        Engine();
        ~Engine();

        // Initialize the engine with a window of given width, height, and title.
        void init(int width, int height, const char* title);

        // Set the clear color for the screen.
        void set_clear_color(int r, int g, int b);

        // Clear the screen to a default color (black) and get ready to draw.
        void begin_frame();

        // Present what has been drawn.
        void end_frame();

        // Draw a simple filled rectangle (we'll use a fixed color for now).
        void draw_rect(int x, int y, int w, int h, int r, int g, int b);

        // Sprite drawing stub for later.
        void draw_sprite(int texture_id, int x, int y, int w, int h);

        // Poll all pending events and return them.
        std::vector<Event> poll_events();
        
        // Load a TTF font from file at specified point size.
        int load_font(const char* path, int pt_size);

        // Draw text at specified position.
        void draw_text(const char* text, int x, int y, int r, int g, int b, int font_id = -1);

        // Capture the current frame into an image file (BMP for now).
        // Returns true on success, false on failure.
        bool capture_frame(const char* path);

        // Draw a filled rectangle with RGBA color (supports transparency).
        void draw_rect_rgba(int x, int y, int w, int h, int r, int g, int b, int a);

    private:
        SDL_Window* window_; // The main application window.
        SDL_Renderer* renderer_; // The renderer for drawing.
        bool initialized_; // Whether the engine has been initialized.
        TTF_Font* font_; // The current font for text rendering.
        SDL_Color clear_color_; // The clear color for the screen.
        std::vector<TTF_Font*> fonts_; // Loaded fonts.
        int default_font_id_; // Default font index.
    };

} // namespace mini

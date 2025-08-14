#!/usr/bin/env python3
"""
Riftbound Cards Quiz Widget

This widget implements the card name quiz feature where users are presented
with card images (with names blanked out) and must guess the card names.
"""

import sys
import json
import random
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QGroupBox, QMessageBox,
    QProgressBar, QTextEdit, QSplitter, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import (
    QPixmap, QPainter, QBrush, QColor, QFont, QPen, QTransform
)

from src.models.piltover_card_database import PiltoverCardDatabase, PiltoverCard


class QuizQuestion:
    """Represents a single quiz question"""
    
    def __init__(self, card: PiltoverCard, image_path: str):
        self.card = card
        self.image_path = image_path
        self.user_answer = ""
        self.is_correct = False
        self.answered = False
        self.answer_time = 0.0
        self.last_rating: Optional[int] = None


class SRSState:
    """Per-card spaced repetition state for SM-2 scheduling"""
    
    def __init__(self, ef: float = 2.5, repetitions: int = 0, interval_days: int = 0, due_iso: Optional[str] = None):
        self.easiness_factor: float = ef
        self.repetitions: int = repetitions
        self.interval_days: int = interval_days
        # Store due date as ISO string for JSON persistence
        self.due_iso: str = due_iso or datetime.now().date().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "ef": self.easiness_factor,
            "repetitions": self.repetitions,
            "interval_days": self.interval_days,
            "due": self.due_iso,
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "SRSState":
        return SRSState(
            ef=float(data.get("ef", 2.5)),
            repetitions=int(data.get("repetitions", 0)),
            interval_days=int(data.get("interval_days", 0)),
            due_iso=str(data.get("due")) if data.get("due") else datetime.now().date().isoformat(),
        )


class QuizImageWidget(QLabel):
    """Widget for displaying quiz card images with blanked out names"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap: Optional[QPixmap] = None
        self.blanked_pixmap: Optional[QPixmap] = None
        self.name_coordinates: List[Dict] = []
        self.setFixedSize(300, 420)  # Fixed card dimensions - no expansion
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px solid #ccc; border-radius: 8px;")
        
        print("🖼️ QuizImageWidget initialized")
    
    def load_card_image(self, image_path: str, coordinates: List[Dict] = None, card_format: str = "classic") -> bool:
        """Load a card image and blank out the name areas"""
        try:
            original_pixmap = QPixmap(image_path)
            if original_pixmap.isNull():
                print(f"❌ Failed to load quiz image: {image_path}")
                return False
            
            # Transform coordinates for battlefield cards before rotation
            transformed_coordinates = coordinates or []
            if card_format == "battlefield" and coordinates:
                orig_width = original_pixmap.width()
                orig_height = original_pixmap.height()
                transformed_coordinates = []
                
                for coord in coordinates:
                    # Transform coordinates for 90° clockwise rotation
                    new_x = orig_height - coord['y'] - coord['height']
                    new_y = coord['x']
                    new_width = coord['height']
                    new_height = coord['width']
                    
                    transformed_coordinates.append({
                        'x': new_x,
                        'y': new_y, 
                        'width': new_width,
                        'height': new_height
                    })
            
            # Rotate battlefield cards 90 degrees clockwise for easier reading
            if card_format == "battlefield":
                transform = QTransform()
                transform.rotate(90)
                original_pixmap = original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
                print(f"🔄 Rotated battlefield card 90° clockwise for easier reading")
            
            self.original_pixmap = original_pixmap
            self.name_coordinates = transformed_coordinates
            self.create_blanked_image()
            print(f"✅ Loaded quiz image: {image_path}")
            return True
        
        except Exception as e:
            print(f"❌ Error loading quiz image {image_path}: {e}")
            return False
    
    def create_blanked_image(self):
        """Create a version of the image with names blanked out"""
        if not self.original_pixmap:
            return
        
        # Create a copy of the original pixmap
        self.blanked_pixmap = QPixmap(self.original_pixmap)
        
        if self.name_coordinates:
            # Paint black rectangles over name areas
            painter = QPainter(self.blanked_pixmap)
            painter.setBrush(QBrush(QColor(0, 0, 0)))  # Black brush
            painter.setPen(Qt.PenStyle.NoPen)
            
            for coord in self.name_coordinates:
                rect = QRect(coord['x'], coord['y'], coord['width'], coord['height'])
                painter.drawRect(rect)
                print(f"🖤 Blanked name area: {rect}")
            
            painter.end()
        
        # Scale the image to fit the widget while maintaining aspect ratio
        scaled_pixmap = self.blanked_pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
    
    def reveal_answer(self):
        """Show the original image with the card name visible"""
        if self.original_pixmap:
            # Scale while maintaining aspect ratio
            scaled_pixmap = self.original_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
            print("✨ Revealed card name")
    
    def resizeEvent(self, event):
        """Handle widget resize by rescaling the image"""
        super().resizeEvent(event)
        if self.blanked_pixmap:
            # Always maintain aspect ratio and don't stretch beyond widget bounds
            scaled_pixmap = self.blanked_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)


class QuizWidget(QWidget):
    """Main quiz widget implementing the 20-question card name quiz"""
    
    def __init__(self, database: PiltoverCardDatabase, parent=None):
        super().__init__(parent)
        self.database = database
        
        # Quiz state
        self.questions: List[QuizQuestion] = []
        self.current_question_index = 0
        self.quiz_active = False
        self.question_start_time = 0.0
        self.session_size: int = 20
        self.daily_new_limit: int = 10
        self.max_relearn_per_card: int = 2
        self.relearn_spacing: int = 5
        self.relearn_counts: Dict[str, int] = {}
        
        # Load card name coordinates
        self.card_coordinates = self.load_card_coordinates()
        
        # Load SRS progress
        self.srs_progress_path = Path("srs_progress.json")
        self.srs_progress: Dict[str, SRSState] = self.load_srs_progress()
        
        # Daily state to enforce new-card limit across multiple sessions
        self.daily_state_path = Path("srs_daily_state.json")
        self.daily_state: Dict = self.load_daily_state()
        
        # Ensure this widget can receive keyboard focus for rating shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.setup_ui()
        print("🧠 QuizWidget initialized")
    
    def setup_ui(self):
        """Set up the quiz user interface"""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Header section
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("🧠 Riftbound Cards Quiz")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; margin-bottom: 5px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Test your knowledge of Riftbound card names!")
        subtitle_label.setFont(QFont("Arial", 11))
        subtitle_label.setStyleSheet("color: #666666;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        # SRS summary and actions
        header_actions = QHBoxLayout()
        self.srs_summary_label = QLabel("")
        self.srs_summary_label.setStyleSheet("color: #555;")
        header_actions.addWidget(self.srs_summary_label)
        header_actions.addStretch()
        
        self.reset_button = QPushButton("Reset Learning")
        self.reset_button.setStyleSheet("padding: 6px 10px;")
        self.reset_button.clicked.connect(self.reset_all_srs)
        header_actions.addWidget(self.reset_button)

        # Controls to expand today's new-cap for intensive study
        self.expand10_button = QPushButton("Learn +10 today")
        self.expand10_button.setStyleSheet("padding: 6px 10px;")
        self.expand10_button.clicked.connect(lambda: self.expand_today_new_cap(10))
        header_actions.addWidget(self.expand10_button)
        
        self.expand_all_button = QPushButton("Learn all today")
        self.expand_all_button.setStyleSheet("padding: 6px 10px;")
        self.expand_all_button.clicked.connect(self.expand_today_new_to_all)
        header_actions.addWidget(self.expand_all_button)
        
        header_layout.addLayout(header_actions)
        
        layout.addWidget(header_frame)
        
        # Progress section
        progress_frame = QFrame()
        progress_layout = QHBoxLayout(progress_frame)
        
        self.progress_label = QLabel("Ready to start quiz")
        self.progress_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 20)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
        
        # Main quiz area - use splitter for layout
        quiz_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Image and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Quiz image
        image_group = QGroupBox("Card Image")
        image_layout = QVBoxLayout(image_group)
        image_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the card in its container
        
        self.quiz_image = QuizImageWidget()
        image_layout.addWidget(self.quiz_image)
        
        left_layout.addWidget(image_group)
        
        # Answer input
        answer_group = QGroupBox("Your Answer")
        answer_layout = QVBoxLayout(answer_group)
        
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Enter the card name and press Enter...")
        self.answer_input.setFont(QFont("Arial", 14))
        self.answer_input.returnPressed.connect(self.handle_enter_key)
        answer_layout.addWidget(self.answer_input)
        
        # Enter key instructions
        enter_instructions = QLabel("Press Enter to submit answer, then Enter again for next question")
        enter_instructions.setFont(QFont("Arial", 10))
        enter_instructions.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        answer_layout.addWidget(enter_instructions)
        
        # Word matching instructions
        word_instructions = QLabel("💡 Tip: Include all main words (commas optional, order doesn't matter)")
        word_instructions.setFont(QFont("Arial", 9))
        word_instructions.setStyleSheet("color: #888; font-style: italic; padding: 2px;")
        answer_layout.addWidget(word_instructions)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Study")
        self.start_button.clicked.connect(self.start_quiz)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        self.submit_button = QPushButton("Submit Answer")
        self.submit_button.clicked.connect(self.submit_answer)
        self.submit_button.setEnabled(False)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0e6e0e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.submit_button)
        
        self.next_button = QPushButton("Next Question")
        self.next_button.clicked.connect(self.next_question)
        self.next_button.setEnabled(False)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #d83b01;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #a92d01;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.next_button)
        
        answer_layout.addLayout(button_layout)
        left_layout.addWidget(answer_group)
        
        # Rating controls (SM-2 quality 0-5)
        self.rating_group = QGroupBox("Rate your recall (0=Again … 5=Perfect)")
        rating_layout = QHBoxLayout(self.rating_group)
        self.rating_buttons: Dict[int, QPushButton] = {}
        for q in range(0, 6):
            btn = QPushButton(str(q))
            btn.setFixedWidth(36)
            btn.setEnabled(False)
            btn.clicked.connect(lambda _=False, quality=q: self.on_rating_clicked(quality))
            self.rating_buttons[q] = btn
            rating_layout.addWidget(btn)
        self.rating_group.setVisible(False)
        left_layout.addWidget(self.rating_group)
        
        # Right side - Results and feedback
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Current question feedback
        feedback_group = QGroupBox("Question Feedback")
        feedback_layout = QVBoxLayout(feedback_group)
        
        self.feedback_label = QLabel("Answer the current question to see feedback")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setFont(QFont("Arial", 12))
        self.feedback_label.setStyleSheet("padding: 10px;")
        feedback_layout.addWidget(self.feedback_label)
        
        right_layout.addWidget(feedback_group, 0)  # No stretch for feedback
        
        # Quiz results summary - give it more space
        results_group = QGroupBox("Quiz Progress")
        results_layout = QVBoxLayout(results_group)
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setHtml("<i>Start a quiz to see your progress</i>")
        # Allow the results display to expand and use available space
        self.results_display.setSizePolicy(QSizePolicy.Policy.Preferred, 
                                          QSizePolicy.Policy.Expanding)
        results_layout.addWidget(self.results_display)
        
        right_layout.addWidget(results_group, 1)  # Give stretch to results
        
        # Add panels to splitter
        quiz_splitter.addWidget(left_panel)
        quiz_splitter.addWidget(right_panel)
        quiz_splitter.setSizes([600, 400])
        
        layout.addWidget(quiz_splitter)
        
        # Instructions (collapsible)
        instructions_group = QGroupBox("Instructions")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = QLabel("""
        <b>How to play:</b><br>
        1. Click "Start Quiz" to begin a 20-question quiz<br>
        2. Look at the card image with the name blanked out<br>
        3. Type your guess for the card name in the text box<br>
        4. Press Enter or click "Submit Answer" to check your answer<br>
        5. Review the feedback and click "Next Question" to continue<br>
        6. After 20 questions, see your final score and review all answers<br><br>
        <b>Scoring:</b> Name matching is case-insensitive and ignores spaces and punctuation.
        """)
        instructions_text.setWordWrap(True)
        instructions_text.setStyleSheet("padding: 10px;")
        instructions_layout.addWidget(instructions_text)
        
        layout.addWidget(instructions_group)
        
        # Set the content widget to the scroll area and add to main layout
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Update initial SRS summary
        self.update_srs_summary()
    
    def load_card_coordinates(self) -> Dict:
        """Load card name coordinate data from the coordinate tool"""
        coordinates_file = Path("card_name_coordinates.json")
        try:
            if coordinates_file.exists():
                with open(coordinates_file, 'r', encoding='utf-8') as f:
                    coordinates = json.load(f)
                print(f"📂 Loaded {len(coordinates)} coordinate sets")
                return coordinates
            else:
                print("📄 No coordinate data found - names won't be blanked in quiz")
                return {}
        except Exception as e:
            print(f"❌ Error loading coordinates: {e}")
            return {}
    
    def start_quiz(self):
        """Start a new study session using SM-2 scheduling"""
        print("🚀 Starting new study session...")
        
        # Get all available cards from database
        try:
            # Reset daily state if date changed
            self.reset_daily_state_if_needed()
            introduced_today: set[str] = set(self.daily_state.get("introduced_today", []))
            new_taken_today: int = int(self.daily_state.get("new_taken_today", 0))
            cap_today = int(self.daily_state.get("new_cap_today", self.daily_new_limit))
            remaining_new_quota: int = max(0, cap_today - new_taken_today)
            
            all_cards = self.database.get_all_variants(limit=None)
            if len(all_cards) < 5:
                QMessageBox.warning(self, "Warning", f"Need at least 20 cards in database. Found only {len(all_cards)}.")
                return
            
            # Build study queue: due cards first, then new cards up to session size
            today = datetime.now().date()
            due_cards: List[PiltoverCard] = []
            new_cards: List[PiltoverCard] = []
            
            for card in all_cards:
                vid = str(card.variant_id)
                state = self.srs_progress.get(vid)
                if state is None:
                    # Exclude new cards already introduced today in previous sessions
                    if vid not in introduced_today:
                        new_cards.append(card)
                else:
                    try:
                        due_date = datetime.fromisoformat(state.due_iso).date()
                    except Exception:
                        due_date = today
                    if due_date <= today:
                        due_cards.append(card)
            
            random.shuffle(due_cards)
            # Sort new cards by variant number ascending to start with earliest ones
            def variant_key(c: PiltoverCard) -> Tuple[str, int, str]:
                vn = c.variant_number or ""
                parts = vn.split('-')
                prefix = parts[0] if len(parts) > 0 else ""
                num_str = parts[1] if len(parts) > 1 else "0"
                # Handle suffix like 300s -> strip trailing non-digits for ordering
                digits = ''.join(ch for ch in num_str if ch.isdigit()) or "0"
                suffix = ''.join(ch for ch in num_str if not ch.isdigit())
                return (prefix, int(digits), suffix)
            new_cards.sort(key=variant_key)
            selected_cards: List[PiltoverCard] = []
            
            # First take due cards
            for c in due_cards:
                if len(selected_cards) >= self.session_size:
                    break
                selected_cards.append(c)
            
            # Then take new cards up to daily limit
            new_taken = 0
            for c in new_cards:
                if len(selected_cards) >= self.session_size:
                    break
                if new_taken >= remaining_new_quota:
                    break
                selected_cards.append(c)
                new_taken += 1
            
            # Persist daily introduced set and counter
            if new_taken > 0:
                for c in selected_cards[-new_taken:]:
                    self.daily_state.setdefault("introduced_today", [])
                    vid = str(c.variant_id)
                    if vid not in self.daily_state["introduced_today"]:
                        self.daily_state["introduced_today"].append(vid)
                self.daily_state["new_taken_today"] = int(self.daily_state.get("new_taken_today", 0)) + new_taken
                self.save_daily_state()

            # Create quiz questions
            self.questions = []
            for card in selected_cards:
                image_path = self.get_card_image_path(card)
                if image_path and Path(image_path).exists():
                    question = QuizQuestion(card, image_path)
                    self.questions.append(question)
                    print(f"➕ Added quiz question: {card.name}")
            
            if len(self.questions) < 20:
                # If we couldn't find enough images, fill with available ones
                while len(self.questions) < 20 and len(all_cards) > len(self.questions):
                    for card in all_cards:
                        if len(self.questions) >= 20:
                            break
                        if not any(q.card.variant_id == card.variant_id for q in self.questions):
                            image_path = self.get_card_image_path(card)
                            if image_path and Path(image_path).exists():
                                question = QuizQuestion(card, image_path)
                                self.questions.append(question)
                                print(f"➕ Added backup quiz question: {card.name}")
            
            if len(self.questions) < 5:
                QMessageBox.warning(self, "Warning", f"Only found {len(self.questions)} cards with images. Need at least 5 to start quiz.")
                return
            
            # Trim to session size
            self.questions = self.questions[: self.session_size]
            
            # Initialize quiz state
            self.current_question_index = 0
            self.quiz_active = True
            self.relearn_counts = {}
            
            # Update UI
            self.start_button.setEnabled(False)
            self.submit_button.setEnabled(True)
            self.answer_input.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(self.questions))
            
            # Start first question
            self.show_current_question()
            
            print(f"✅ Study session started with {len(self.questions)} items (due: {len(due_cards)}, new used now: {new_taken}, remaining new today: {max(0, int(self.daily_state.get('new_cap_today', self.daily_new_limit)) - int(self.daily_state.get('new_taken_today', 0)))} )")
            self.update_srs_summary()
        
        except Exception as e:
            print(f"❌ Error starting quiz: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start quiz: {str(e)}")
    
    def get_card_image_path(self, card: PiltoverCard) -> Optional[str]:
        """Get the file path for a card's image"""
        try:
            base_path = Path(__file__).resolve().parents[2] / "card_img"
            
            # Get the set prefix and card number
            if not card.variant_number:
                return None
            
            prefix = card.variant_number.split('-')[0]
            # Handle star suffix (e.g., OGN-300* -> OGN-300s.webp)
            file_id = card.variant_number.replace('*', 's')
            
            image_path = base_path / prefix / f"{file_id}.webp"
            
            if image_path.exists():
                return str(image_path)
            else:
                print(f"⚠️ Image not found: {image_path}")
                return None
        
        except Exception as e:
            print(f"❌ Error getting image path for {card.name}: {e}")
            return None
    
    def show_current_question(self):
        """Display the current quiz question"""
        if not self.quiz_active or self.current_question_index >= len(self.questions):
            return
        
        question = self.questions[self.current_question_index]
        
        # Update progress
        self.progress_label.setText(f"Item {self.current_question_index + 1} of {len(self.questions)}")
        self.progress_bar.setValue(self.current_question_index)
        
        # Get coordinate data for this card if available
        coordinates = self.get_card_coordinates(question.card)
        
        # Detect card format (battlefield cards should be displayed horizontally)
        card_format = self.detect_card_format(question.card)
        
        # Load the card image
        if self.quiz_image.load_card_image(question.image_path, coordinates, card_format):
            print(f"📸 Showing question {self.current_question_index + 1}: {question.card.name}")
        else:
            print(f"❌ Failed to load image for question {self.current_question_index + 1}")
        
        # Clear previous answer
        self.answer_input.clear()
        self.answer_input.setFocus()
        
        # Update feedback
        self.feedback_label.setText("Enter your guess for this card's name (Press Enter to submit)")
        
        # Reset button states
        self.submit_button.setEnabled(True)
        self.next_button.setEnabled(False)
        self.set_rating_enabled(False)
        self.rating_group.setVisible(False)
        
        # Record question start time
        self.question_start_time = datetime.now().timestamp()
    
    def detect_card_format(self, card: PiltoverCard) -> str:
        """Detect if a card is classic or battlefield format based on card type"""
        if card.type == 'Battlefield':
            print(f"🏛️ Detected battlefield card: {card.name} ({card.variant_number}) - type: {card.type}")
            return "battlefield"
        else:
            print(f"🃏 Detected classic card: {card.name} ({card.variant_number}) - type: {card.type}")
            return "classic"
    
    def get_card_coordinates(self, card: PiltoverCard) -> List[Dict]:
        """Get name coordinate data for a specific card"""
        if not self.card_coordinates:
            return []
        
        # Try to find coordinates by card name or variant number
        card_name = card.name.replace(' ', '_').replace(':', '').replace(',', '')
        
        # Try different keys
        possible_keys = [
            f"{card_name}_classic",
            f"{card_name}_battlefield",
            f"{card.variant_number}_classic",
            f"{card.variant_number}_battlefield",
        ]
        
        for key in possible_keys:
            if key in self.card_coordinates:
                coords = self.card_coordinates[key].get('coordinates', [])
                print(f"📍 Found {len(coords)} coordinate rectangles for {card.name}")
                return coords
        
        print(f"📍 No coordinates found for {card.name}")
        return []
    
    def submit_answer(self):
        """Submit the current answer and show feedback"""
        if not self.quiz_active or self.current_question_index >= len(self.questions):
            return
        
        question = self.questions[self.current_question_index]
        user_answer = self.answer_input.text().strip()
        
        if not user_answer:
            QMessageBox.warning(self, "Warning", "Please enter an answer!")
            return
        
        # Record answer
        question.user_answer = user_answer
        question.answered = True
        question.answer_time = datetime.now().timestamp() - self.question_start_time
        
        # Check if answer is correct
        question.is_correct = self.check_answer(user_answer, question.card.name)
        
        # Show feedback
        self.show_answer_feedback(question)
        
        # Reveal the actual card name
        self.quiz_image.reveal_answer()
        
        # Update UI state
        self.submit_button.setEnabled(False)
        # Require a rating before moving on
        self.next_button.setEnabled(False)
        # Keep input enabled but clear it; focus will be restored on next question
        self.answer_input.clear()
        
        # Update results display
        self.update_results_display()
        
        # Show and enable rating controls
        self.rating_group.setVisible(True)
        self.set_rating_enabled(True)
        
        # Move focus away from the input so 0–5 shortcuts work
        self.answer_input.clearFocus()
        self.setFocus()
        
        print(f"📝 Answer submitted: '{user_answer}' for '{question.card.name}' - {'✅ Correct' if question.is_correct else '❌ Wrong'}")
    
    def check_answer(self, user_answer: str, correct_answer: str) -> bool:
        """Check if the user's answer matches the correct card name"""
        # Normalize function that removes commas but keeps other punctuation for word separation
        def normalize_for_words(text: str) -> str:
            # Remove commas but keep spaces and other punctuation for word separation
            text = text.replace(',', '')
            return text.lower().strip()
        
        def get_words(text: str) -> set:
            # Extract words, removing punctuation but keeping alphanumeric characters
            words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
            return set(words)
        
        user_normalized = normalize_for_words(user_answer)
        correct_normalized = normalize_for_words(correct_answer)
        
        # Get word sets for both answers
        user_words = get_words(user_normalized)
        correct_words = get_words(correct_normalized)
        
        print(f"🔍 Checking answer: '{user_answer}' vs '{correct_answer}'")
        
        # Check if all correct words are present in user answer
        if correct_words.issubset(user_words):
            print(f"✅ All required words found")
            return True
        
        # Check if all user words are present in correct answer (handles partial answers)
        if user_words.issubset(correct_words) and len(user_words) >= len(correct_words) * 0.7:
            print(f"✅ Sufficient word match (70%+ coverage)")
            return True
        
        # Calculate word overlap percentage
        if len(correct_words) > 0:
            overlap = len(user_words.intersection(correct_words))
            overlap_percentage = overlap / len(correct_words)
            print(f"📊 Word overlap: {overlap}/{len(correct_words)} ({overlap_percentage:.1%})")
            
            # Accept if at least 80% of words match
            if overlap_percentage >= 0.8:
                print(f"✅ High word overlap accepted")
                return True
        
        print(f"❌ Insufficient word match")
        return False
    
    def show_answer_feedback(self, question: QuizQuestion):
        """Show feedback for the current answer"""
        if question.is_correct:
            feedback = f"<div style='color: green; font-weight: bold;'>✅ Correct!</div>"
            feedback += f"<div>You answered: <b>{question.user_answer}</b></div>"
            feedback += f"<div>Correct answer: <b>{question.card.name}</b></div>"
            feedback += f"<div>Time: {question.answer_time:.1f} seconds</div>"
            feedback += f"<div style='font-style: italic; color: #666; margin-top: 10px;'>Rate your recall (0–5) to continue</div>"
        else:
            feedback = f"<div style='color: red; font-weight: bold;'>❌ Incorrect</div>"
            feedback += f"<div>You answered: <b>{question.user_answer}</b></div>"
            feedback += f"<div>Correct answer: <b>{question.card.name}</b></div>"
            feedback += f"<div>Time: {question.answer_time:.1f} seconds</div>"
            feedback += f"<div style='font-style: italic; color: #666; margin-top: 10px;'>Rate your recall (0–5) to continue</div>"
        
        # Add card details
        feedback += f"<hr><div><b>Card Details:</b></div>"
        feedback += f"<div>Set: {question.card.set_name}</div>"
        feedback += f"<div>Type: {question.card.type}</div>"
        feedback += f"<div>Rarity: {question.card.rarity}</div>"
        
        self.feedback_label.setText(feedback)
    
    def next_question(self):
        """Move to the next question or finish the quiz"""
        self.current_question_index += 1
        
        if self.current_question_index >= len(self.questions):
            self.finish_quiz()
        else:
            # Reset answer input for next question
            self.answer_input.setEnabled(True)
            self.show_current_question()
    
    def finish_quiz(self):
        """Finish the quiz and show final results"""
        self.quiz_active = False
        
        # Calculate final score
        correct_answers = sum(1 for q in self.questions if q.is_correct)
        total_questions = len(self.questions)
        score_percentage = (correct_answers / total_questions) * 100
        
        # Update progress
        self.progress_label.setText(f"Quiz Complete! Score: {correct_answers}/{total_questions} ({score_percentage:.1f}%)")
        self.progress_bar.setValue(total_questions)
        
        # Show completion message
        if score_percentage >= 80:
            message = "🎉 Excellent work!"
        elif score_percentage >= 60:
            message = "👍 Good job!"
        elif score_percentage >= 40:
            message = "📖 Keep studying!"
        else:
            message = "💪 Practice makes perfect!"
        
        self.feedback_label.setText(f"""
        <div style='text-align: center; font-size: 16px; font-weight: bold;'>
            {message}<br>
            Final Score: {correct_answers}/{total_questions} ({score_percentage:.1f}%)
        </div>
        """)
        
        # Reset UI
        self.start_button.setEnabled(True)
        self.submit_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.answer_input.setEnabled(False)
        self.answer_input.clear()
        
        # Clear image
        self.quiz_image.setPixmap(QPixmap())  # Clear the image
        
        print(f"🏁 Quiz completed! Score: {correct_answers}/{total_questions} ({score_percentage:.1f}%)")
        self.update_srs_summary()
    
    def update_results_display(self):
        """Update the results display with current quiz progress"""
        if not self.questions:
            return
        
        html = "<h4>Study Progress:</h4><table border='1' cellpadding='5'>"
        html += "<tr><th>#</th><th>Card</th><th>Your Answer</th><th>Result</th><th>Time</th><th>Rating</th></tr>"
        
        for i, question in enumerate(self.questions):
            if question.answered:
                result_icon = "✅" if question.is_correct else "❌"
                result_color = "green" if question.is_correct else "red"
                time_str = f"{question.answer_time:.1f}s"
                rating_str = "-" if question.last_rating is None else str(question.last_rating)
                
                html += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{question.card.name}</td>
                    <td>{question.user_answer}</td>
                    <td style='color: {result_color}; font-weight: bold;'>{result_icon}</td>
                    <td>{time_str}</td>
                    <td>{rating_str}</td>
                </tr>
                """
            elif i == self.current_question_index:
                html += f"""
                <tr style='background-color: #fff3cd;'>
                    <td>{i+1}</td>
                    <td>{question.card.name}</td>
                    <td><i>Current question</i></td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                """
            else:
                html += f"""
                <tr style='color: #666;'>
                    <td>{i+1}</td>
                    <td>???</td>
                    <td><i>Not answered</i></td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                """
        
        html += "</table>"
        
        # Add summary stats
        answered_count = sum(1 for q in self.questions if q.answered)
        correct_count = sum(1 for q in self.questions if q.is_correct)
        
        if answered_count > 0:
            html += f"<br><b>Progress:</b> {answered_count}/{len(self.questions)} answered"
            html += f"<br><b>Score:</b> {correct_count}/{answered_count} correct ({(correct_count/answered_count)*100:.1f}%)"
        
        self.results_display.setHtml(html)
    
    def handle_enter_key(self):
        """Handle Enter key press - submit answer or go to next question"""
        if self.submit_button.isEnabled():
            print("🔑 First Enter - submitting answer")
            self.submit_answer()
        elif self.rating_group.isVisible():
            # Waiting for a rating; ignore Enter to encourage using 0–5 keys
            return
        elif self.next_button.isEnabled():
            print("🔑 Second Enter - going to next question")
            self.next_question()

    def keyPressEvent(self, event):
        """Keyboard shortcuts for rating 0–5 while rating controls are visible"""
        if self.rating_group.isVisible():
            key_to_quality = {
                Qt.Key.Key_0: 0,
                Qt.Key.Key_1: 1,
                Qt.Key.Key_2: 2,
                Qt.Key.Key_3: 3,
                Qt.Key.Key_4: 4,
                Qt.Key.Key_5: 5,
            }
            quality = key_to_quality.get(event.key())
            if quality is not None:
                self.on_rating_clicked(quality)
                return
        super().keyPressEvent(event)

    def set_rating_enabled(self, enabled: bool):
        for btn in self.rating_buttons.values():
            btn.setEnabled(enabled)

    def on_rating_clicked(self, quality: int):
        """Apply SM-2 update based on user quality rating (0–5) and advance"""
        if not self.quiz_active or self.current_question_index >= len(self.questions):
            return
        question = self.questions[self.current_question_index]
        question.last_rating = quality
        
        # Update SRS state for this card
        self.apply_sm2_update(str(question.card.variant_id), quality)
        self.save_srs_progress()
        self.update_srs_summary()
        
        # Intra-day relearn queue for difficult items
        if quality <= 2:
            vid = str(question.card.variant_id)
            count = self.relearn_counts.get(vid, 0)
            if count < self.max_relearn_per_card:
                # Reinsert a new question instance a few items ahead to create spacing
                insert_index = min(len(self.questions), self.current_question_index + 1 + self.relearn_spacing)
                reinjected = QuizQuestion(question.card, question.image_path)
                self.questions.insert(insert_index, reinjected)
                self.relearn_counts[vid] = count + 1
                # Update progress bar maximum and results view
                self.progress_bar.setMaximum(len(self.questions))
                self.update_results_display()
                print(f"🔁 Scheduled relearn for '{question.card.name}' at position {insert_index + 1} (#{self.relearn_counts[vid]} in-session)")
        
        # Hide rating and go to next item
        self.set_rating_enabled(False)
        self.rating_group.setVisible(False)
        self.next_question()

    def load_srs_progress(self) -> Dict[str, SRSState]:
        try:
            if self.srs_progress_path.exists():
                with open(self.srs_progress_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                progress: Dict[str, SRSState] = {}
                for vid, state in raw.items():
                    progress[str(vid)] = SRSState.from_dict(state)
                print(f"📚 Loaded SRS progress for {len(progress)} cards")
                return progress
        except Exception as e:
            print(f"❌ Error loading SRS progress: {e}")
        return {}

    def save_srs_progress(self):
        try:
            data = {vid: state.to_dict() for vid, state in self.srs_progress.items()}
            with open(self.srs_progress_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("💾 Saved SRS progress")
        except Exception as e:
            print(f"❌ Error saving SRS progress: {e}")

    def apply_sm2_update(self, variant_id: str, quality: int):
        """Update SRS state for a card using SM-2 algorithm based on quality 0–5"""
        state = self.srs_progress.get(variant_id) or SRSState()
        # Quality bounds
        q = max(0, min(5, int(quality)))
        
        if q < 3:
            # Incorrect recall: reset repetitions; schedule sooner
            state.repetitions = 0
            state.interval_days = 1
        else:
            # Correct recall
            state.repetitions += 1
            if state.repetitions == 1:
                state.interval_days = 1
            elif state.repetitions == 2:
                state.interval_days = 6
            else:
                state.interval_days = int(round(state.interval_days * state.easiness_factor))
        
        # Update EF
        ef = state.easiness_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        state.easiness_factor = max(1.3, ef)
        
        # Compute next due date
        next_due = datetime.now().date() + timedelta(days=state.interval_days)
        state.due_iso = next_due.isoformat()
        
        self.srs_progress[variant_id] = state
        print(f"🗓️ Rated {q}: EF={state.easiness_factor:.2f}, reps={state.repetitions}, interval={state.interval_days}d, due={state.due_iso}")

    def update_srs_summary(self):
        """Update SRS summary label with counts of due/new cards"""
        try:
            all_cards = self.database.get_all_variants(limit=None)
            today = datetime.now().date()
            due = 0
            new = 0
            for card in all_cards:
                vid = str(card.variant_id)
                state = self.srs_progress.get(vid)
                if state is None:
                    new += 1
                else:
                    try:
                        due_date = datetime.fromisoformat(state.due_iso).date()
                    except Exception:
                        due_date = today
                    if due_date <= today:
                        due += 1
            cap = int(self.daily_state.get("new_cap_today", self.daily_new_limit))
            remaining_new = max(0, cap - int(self.daily_state.get("new_taken_today", 0)))
            self.srs_summary_label.setText(f"Due today: {due} • New available today: {remaining_new} (of {cap})")
        except Exception:
            self.srs_summary_label.setText("")

    def reset_all_srs(self):
        """Reset all learning progress after confirmation"""
        confirm = QMessageBox.question(
            self,
            "Reset Learning",
            "This will clear all learning progress (EF, intervals, due dates). Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.srs_progress = {}
            self.save_srs_progress()
            self.update_srs_summary()
            QMessageBox.information(self, "Reset Learning", "All learning progress has been reset.")

    # -------- Daily state persistence (new-cards introduced per day) --------
    def load_daily_state(self) -> Dict:
        try:
            if self.daily_state_path.exists():
                with open(self.daily_state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"❌ Error loading daily state: {e}")
        return {"date": datetime.now().date().isoformat(), "introduced_today": [], "new_taken_today": 0, "new_cap_today": self.daily_new_limit}

    def save_daily_state(self):
        try:
            with open(self.daily_state_path, "w", encoding="utf-8") as f:
                json.dump(self.daily_state, f, ensure_ascii=False, indent=2)
            print("💾 Saved daily state")
        except Exception as e:
            print(f"❌ Error saving daily state: {e}")

    def reset_daily_state_if_needed(self):
        try:
            today = datetime.now().date().isoformat()
            if self.daily_state.get("date") != today:
                self.daily_state = {"date": today, "introduced_today": [], "new_taken_today": 0, "new_cap_today": self.daily_new_limit}
                self.save_daily_state()
        except Exception as e:
            print(f"❌ Error resetting daily state: {e}")

    # Expand today's new-card cap helpers
    def expand_today_new_cap(self, increment: int):
        try:
            cap = int(self.daily_state.get("new_cap_today", self.daily_new_limit))
            self.daily_state["new_cap_today"] = cap + max(0, int(increment))
            self.save_daily_state()
            self.update_srs_summary()
        except Exception as e:
            print(f"❌ Error expanding new cap: {e}")

    def expand_today_new_to_all(self):
        try:
            # Set cap to a large number to allow entire deck today
            self.daily_state["new_cap_today"] = 10_000_000
            self.save_daily_state()
            self.update_srs_summary()
        except Exception as e:
            print(f"❌ Error expanding new cap to all: {e}")

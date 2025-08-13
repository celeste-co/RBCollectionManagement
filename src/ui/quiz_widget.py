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
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QGroupBox, QMessageBox,
    QProgressBar, QTextEdit, QSplitter, QGridLayout
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


class QuizImageWidget(QLabel):
    """Widget for displaying quiz card images with blanked out names"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap: Optional[QPixmap] = None
        self.blanked_pixmap: Optional[QPixmap] = None
        self.name_coordinates: List[Dict] = []
        self.setMinimumSize(300, 420)  # Typical card dimensions
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
        
        # Scale the image to fit the widget
        scaled_pixmap = self.blanked_pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
    
    def reveal_answer(self):
        """Show the original image with the card name visible"""
        if self.original_pixmap:
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
            scaled_pixmap = self.blanked_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)


class QuizWidget(QWidget):
    """Main quiz widget implementing the 10-question card name quiz"""
    
    def __init__(self, database: PiltoverCardDatabase, parent=None):
        super().__init__(parent)
        self.database = database
        
        # Quiz state
        self.questions: List[QuizQuestion] = []
        self.current_question_index = 0
        self.quiz_active = False
        self.question_start_time = 0.0
        
        # Load card name coordinates
        self.card_coordinates = self.load_card_coordinates()
        
        self.setup_ui()
        print("🧠 QuizWidget initialized")
    
    def setup_ui(self):
        """Set up the quiz user interface"""
        layout = QVBoxLayout(self)
        
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
        
        title_label = QLabel("Riftbound Cards Quiz")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Test your knowledge of Riftbound card names!")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #666666;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
        
        # Progress section
        progress_frame = QFrame()
        progress_layout = QHBoxLayout(progress_frame)
        
        self.progress_label = QLabel("Ready to start quiz")
        self.progress_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 10)
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
        
        self.start_button = QPushButton("Start Quiz")
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
        
        right_layout.addWidget(feedback_group)
        
        # Quiz results summary
        results_group = QGroupBox("Quiz Progress")
        results_layout = QVBoxLayout(results_group)
        
        self.results_display = QTextEdit()
        self.results_display.setMaximumHeight(200)
        self.results_display.setReadOnly(True)
        self.results_display.setHtml("<i>Start a quiz to see your progress</i>")
        results_layout.addWidget(self.results_display)
        
        right_layout.addWidget(results_group)
        
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
        1. Click "Start Quiz" to begin a 10-question quiz<br>
        2. Look at the card image with the name blanked out<br>
        3. Type your guess for the card name in the text box<br>
        4. Press Enter or click "Submit Answer" to check your answer<br>
        5. Review the feedback and click "Next Question" to continue<br>
        6. After 10 questions, see your final score and review all answers<br><br>
        <b>Scoring:</b> Name matching is case-insensitive and ignores spaces and punctuation.
        """)
        instructions_text.setWordWrap(True)
        instructions_text.setStyleSheet("padding: 10px;")
        instructions_layout.addWidget(instructions_text)
        
        layout.addWidget(instructions_group)
    
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
        """Start a new 10-question quiz"""
        print("🚀 Starting new quiz...")
        
        # Get all available cards from database
        try:
            all_cards = self.database.get_all_variants(limit=None)
            if len(all_cards) < 10:
                QMessageBox.warning(self, "Warning", f"Need at least 10 cards in database. Found only {len(all_cards)}.")
                return
            
            # Randomly select 10 cards
            selected_cards = random.sample(all_cards, 10)
            
            # Create quiz questions
            self.questions = []
            for card in selected_cards:
                image_path = self.get_card_image_path(card)
                if image_path and Path(image_path).exists():
                    question = QuizQuestion(card, image_path)
                    self.questions.append(question)
                    print(f"➕ Added quiz question: {card.name}")
            
            if len(self.questions) < 10:
                # If we couldn't find enough images, fill with available ones
                while len(self.questions) < 10 and len(all_cards) > len(self.questions):
                    for card in all_cards:
                        if len(self.questions) >= 10:
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
            
            # Trim to exactly 10 questions (or however many we have)
            self.questions = self.questions[:10]
            
            # Initialize quiz state
            self.current_question_index = 0
            self.quiz_active = True
            
            # Update UI
            self.start_button.setEnabled(False)
            self.submit_button.setEnabled(True)
            self.answer_input.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(self.questions))
            
            # Start first question
            self.show_current_question()
            
            print(f"✅ Quiz started with {len(self.questions)} questions")
        
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
        self.progress_label.setText(f"Question {self.current_question_index + 1} of {len(self.questions)}")
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
        self.next_button.setEnabled(True)
        # Keep input enabled but clear it and set focus for next Enter press
        self.answer_input.clear()
        # Use QTimer to set focus after UI updates are complete
        QTimer.singleShot(50, self.answer_input.setFocus)
        
        # Update results display
        self.update_results_display()
        
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
            feedback += f"<div style='font-style: italic; color: #666; margin-top: 10px;'>Press Enter for next question</div>"
        else:
            feedback = f"<div style='color: red; font-weight: bold;'>❌ Incorrect</div>"
            feedback += f"<div>You answered: <b>{question.user_answer}</b></div>"
            feedback += f"<div>Correct answer: <b>{question.card.name}</b></div>"
            feedback += f"<div>Time: {question.answer_time:.1f} seconds</div>"
            feedback += f"<div style='font-style: italic; color: #666; margin-top: 10px;'>Press Enter for next question</div>"
        
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
    
    def update_results_display(self):
        """Update the results display with current quiz progress"""
        if not self.questions:
            return
        
        html = "<h4>Quiz Progress:</h4><table border='1' cellpadding='5'>"
        html += "<tr><th>Q#</th><th>Card</th><th>Your Answer</th><th>Result</th><th>Time</th></tr>"
        
        for i, question in enumerate(self.questions):
            if question.answered:
                result_icon = "✅" if question.is_correct else "❌"
                result_color = "green" if question.is_correct else "red"
                time_str = f"{question.answer_time:.1f}s"
                
                html += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{question.card.name}</td>
                    <td>{question.user_answer}</td>
                    <td style='color: {result_color}; font-weight: bold;'>{result_icon}</td>
                    <td>{time_str}</td>
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
        elif self.next_button.isEnabled():
            print("🔑 Second Enter - going to next question")
            self.next_question()

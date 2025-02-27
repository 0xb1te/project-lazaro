from flask import Blueprint, request, jsonify
from datetime import datetime
from .utils.qdrant_handler import (
    create_conversation, 
    get_conversations, 
    get_conversation, 
    add_message, 
    delete_conversation, 
    update_conversation_title
)

conversation_bp = Blueprint('conversations', __name__)

@conversation_bp.route("/conversations", methods=["GET"])
def get_all_conversations():
    """Obtiene todas las conversaciones"""
    try:
        conversations = get_conversations()
        return jsonify({"conversations": conversations}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversation_bp.route("/conversations", methods=["POST"])
def create_new_conversation():
    """Crea una nueva conversación"""
    try:
        data = request.json
        title = data.get("title", "Nueva conversación")
        
        conversation = create_conversation(title)
        
        return jsonify(conversation), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversation_bp.route("/conversations/<conversation_id>", methods=["GET"])
def get_single_conversation(conversation_id):
    """Obtiene una conversación específica por su ID"""
    try:
        conversation = get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({"error": "Conversación no encontrada"}), 404
        
        return jsonify(conversation), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversation_bp.route("/conversations/<conversation_id>/messages", methods=["POST"])
def add_conversation_message(conversation_id):
    """Añade un mensaje a una conversación existente"""
    try:
        data = request.json
        role = data.get("role")
        content = data.get("content")
        
        if not role or not content:
            return jsonify({"error": "Se requieren los campos 'role' y 'content'"}), 400
        
        message = add_message(conversation_id, role, content)
        
        if not message:
            return jsonify({"error": "Conversación no encontrada"}), 404
        
        # Si el mensaje es del usuario, procesar la respuesta del asistente
        if role == "user":
            # Importar aquí para evitar circular imports
            from .app import ask_question_internal
            
            # Generar respuesta del asistente
            answer = ask_question_internal(content)
            
            # Añadir respuesta del asistente
            assistant_message = add_message(conversation_id, "assistant", answer)
            
            return jsonify({
                "user_message": message,
                "assistant_message": assistant_message
            }), 200
        
        return jsonify({"message": message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversation_bp.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_single_conversation(conversation_id):
    """Elimina una conversación por su ID"""
    try:
        success = delete_conversation(conversation_id)
        
        if not success:
            return jsonify({"error": "Conversación no encontrada"}), 404
        
        return jsonify({"message": "Conversación eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversation_bp.route("/conversations/<conversation_id>", methods=["PUT"])
def update_conversation(conversation_id):
    """Actualiza el título de una conversación"""
    try:
        data = request.json
        title = data.get("title")
        
        if not title:
            return jsonify({"error": "Se requiere el campo 'title'"}), 400
        
        success = update_conversation_title(conversation_id, title)
        
        if not success:
            return jsonify({"error": "Conversación no encontrada"}), 404
        
        return jsonify({"message": "Título actualizado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
                from flask import jsonify
                from app import app, mongo


                @app.route('/api/legacy-routes-info')
                def legacy_routes_info():
                    return jsonify({'message': 'Routes were consolidated into the main app module. Use /api/* endpoints on the main app.'}), 200

                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return jsonify({'message': 'Teacher updated', 'teacher': teacher.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update teacher error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/teachers/<teacher_id>', methods=['DELETE'])
@jwt_required()
def delete_teacher(teacher_id):
    """Admin-only: delete a teacher user and unassign from classes"""
    try:
        user_id = get_jwt_identity()
        admin = User.query.get(user_id)
        if not admin or admin.role != 'admin':
            return jsonify({'error': 'Administrator privileges required'}), 403

        teacher = User.query.get(teacher_id)
        if not teacher or teacher.role != 'teacher':
            return jsonify({'error': 'Teacher not found'}), 404

        # Unassign classes referencing this teacher
        classes = Class.query.filter_by(teacher_id=teacher.id).all()
        for c in classes:
            c.teacher_id = None
            db.session.add(c)

        # capture old values for audit before deletion
        old_values = teacher.to_dict()
        db.session.delete(teacher)
        db.session.commit()

        # Audit log for delete
        try:
            audit = AuditLog(
                user_id=admin.id,
                action='delete_teacher',
                table_name='users',
                record_id=teacher_id,
                old_values=json.dumps(old_values),
                new_values=None,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return jsonify({'message': 'Teacher deleted'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete teacher error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
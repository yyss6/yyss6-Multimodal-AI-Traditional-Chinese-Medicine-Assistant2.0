@admin_bp.route('/manage_formulas')
@login_required
@admin_required
def manage_formulas():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    per_page = 10
    
    query = Formula.query
    
    # 应用搜索过滤
    if search:
        query = query.filter(
            or_(
                Formula.name.like(f'%{search}%'),
                Formula.pinyin.like(f'%{search}%'),
                Formula.alias.like(f'%{search}%'),
                Formula.functions.like(f'%{search}%')
            )
        )
    
    # 应用分类过滤
    if category:
        query = query.filter(Formula.category == category)
    
    # 按创建时间排序，最新的在前面
    query = query.order_by(Formula.created_at.desc())
    
    # 获取分页结果
    formulas = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取所有分类
    all_categories = db.session.query(Formula.category).distinct().all()
    categories = [cat[0] for cat in all_categories if cat[0]]
    
    # 计算总页数
    total = formulas.total
    total_pages = (total + per_page - 1) // per_page
    
    return render_template(
        'admin/manage_formulas.html',
        formulas=formulas.items,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        categories=categories
    )

@admin_bp.route('/view_formula/<int:formula_id>')
@login_required
@admin_required
def view_formula(formula_id):
    formula = Formula.query.get_or_404(formula_id)
    # 解析方剂组成
    if formula.composition:
        try:
            composition = json.loads(formula.composition)
        except:
            composition = []
    else:
        composition = []
    
    return render_template('admin/view_formula.html', formula=formula, composition=composition)

@admin_bp.route('/edit_formula/<int:formula_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_formula(formula_id):
    formula = Formula.query.get_or_404(formula_id)
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            name = request.form.get('name')
            pinyin = request.form.get('pinyin')
            alias = request.form.get('alias')
            category = request.form.get('category')
            source = request.form.get('source')
            taste_property = request.form.get('taste_property')
            functions = request.form.get('functions')
            indications = request.form.get('indications')
            usage = request.form.get('usage')
            contraindications = request.form.get('contraindications')
            explanation = request.form.get('explanation')
            preparation = request.form.get('preparation')
            
            # 处理方剂组成
            herb_ids = request.form.getlist('herb_id')
            herb_amounts = request.form.getlist('herb_amount')
            herb_notes = request.form.getlist('herb_note')
            
            composition = []
            for i in range(len(herb_ids)):
                if herb_ids[i]:  # 确保有药材ID
                    herb_id = int(herb_ids[i])
                    herb = Herb.query.get(herb_id)
                    if herb:
                        composition.append({
                            'herb_id': herb_id,
                            'herb_name': herb.name,
                            'amount': herb_amounts[i] if i < len(herb_amounts) else '',
                            'note': herb_notes[i] if i < len(herb_notes) else ''
                        })
            
            # 处理图片上传
            if 'image' in request.files and request.files['image'].filename:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
                    # 如果已经有图片，先删除
                    if formula.image_url and os.path.exists(os.path.join(current_app.root_path, formula.image_url.lstrip('/'))):
                        os.remove(os.path.join(current_app.root_path, formula.image_url.lstrip('/')))
                    
                    # 保存新图片
                    filename = secure_filename(f"{name}_{int(time.time())}.{image_file.filename.rsplit('.', 1)[1].lower()}")
                    image_path = os.path.join(current_app.root_path, 'static/uploads/formulas', filename)
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    image_file.save(image_path)
                    formula.image_url = f'/static/uploads/formulas/{filename}'
            
            # 更新方剂信息
            formula.name = name
            formula.pinyin = pinyin
            formula.alias = alias
            formula.category = category
            formula.source = source
            formula.taste_property = taste_property
            formula.functions = functions
            formula.indications = indications
            formula.usage = usage
            formula.contraindications = contraindications
            formula.explanation = explanation
            formula.preparation = preparation
            formula.composition = json.dumps(composition, ensure_ascii=False)
            formula.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('方剂已成功更新！', 'success')
            return redirect(url_for('admin.manage_formulas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新方剂时出错: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_formula', formula_id=formula_id))
    
    # 获取所有中药材
    herbs = Herb.query.order_by(Herb.name).all()
    
    # 解析组成信息
    try:
        composition = json.loads(formula.composition) if formula.composition else []
    except:
        composition = []
    
    return render_template('admin/edit_formula.html', formula=formula, herbs=herbs, composition=composition)

@admin_bp.route('/delete_formula/<int:formula_id>', methods=['POST'])
@login_required
@admin_required
def delete_formula(formula_id):
    formula = Formula.query.get_or_404(formula_id)
    
    try:
        # 删除关联图片
        if formula.image_url and os.path.exists(os.path.join(current_app.root_path, formula.image_url.lstrip('/'))):
            os.remove(os.path.join(current_app.root_path, formula.image_url.lstrip('/')))
        
        # 删除数据库记录
        db.session.delete(formula)
        db.session.commit()
        flash('方剂已成功删除！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除方剂时出错: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_formulas')) 
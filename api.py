from main import app
from flask import Flask, jsonify
from models import db, User, Sponsor, Influencer, Campaign, Ad, Message, Transaction, Rating
from datetime import datetime
from sqlalchemy import func

# API Resources for Stats --------------------------------------------------------------------------------------------------

# For Influencers ----------------------------------------------------------------------------------------------------------

@app.route('/api/influencers/<int:id>/earnings', methods=['GET'])
def get_earnings(id):
    influencer = Influencer.query.get(id)
    earnings = db.session.query(
        func.strftime('%Y-%m', Ad.date_created).label('month'),
        func.sum(Ad.payment_amount).label('total_earnings')
    ).filter(Ad.influencer_id == id, Ad.is_paid).group_by('month').all()
    
    data = [{'month': row.month, 'total_earnings': row.total_earnings} for row in earnings]
    return jsonify(data)

@app.route('/api/influencers/<int:id>/ad_requests_status', methods=['GET'])
def get_ad_requests_status(id):
    ad_requests = db.session.query(
        Ad.status,
        func.count().label('count')
    ).filter(Ad.influencer_id == id).group_by(Ad.status).all()
    
    data = [{'status': row.status, 'count': row.count} for row in ad_requests]
    return jsonify(data)

@app.route('/api/influencers/<int:id>/unpaid_ad_requests', methods=['GET'])
def get_unpaid_ad_requests(id):
    unpaid_requests = db.session.query(
        func.strftime('%Y-%m', Ad.date_created).label('month'),
        func.count().label('count')
    ).filter(Ad.influencer_id == id, Ad.is_paid == False, Ad.status != 'rejected').group_by('month').all()
    
    data = [{'month': row.month, 'count': row.count} for row in unpaid_requests]
    return jsonify(data)

@app.route('/api/influencers/<int:id>/campaign_performance', methods=['GET'])
def get_campaign_performance(id):
    campaigns = db.session.query(
        Campaign.name,
        func.sum(Ad.payment_amount).label('total_earnings')
    ).join(Ad, Campaign.id == Ad.campaign_id).filter(Ad.influencer_id == id, Ad.is_paid).group_by(Campaign.name).all()
    
    data = [{'campaign': row.name, 'total_earnings': row.total_earnings} for row in campaigns]
    return jsonify(data)

@app.route('/api/influencers/<int:id>/ad_request_trends', methods=['GET'])
def get_ad_request_trends(id):
    trends = db.session.query(
        func.strftime('%Y-%m', Ad.date_created).label('month'),
        func.count().label('count')
    ).filter(Ad.influencer_id == id).group_by('month').all()
    
    data = [{'month': row.month, 'count': row.count} for row in trends]
    return jsonify(data)

# For Sponsors ------------------------------------------------------------------------------------------------------------

@app.route('/api/sponsors/<int:id>/monthly_spending', methods=['GET'])
def get_monthly_spending(id):
    spending = db.session.query(
        func.strftime('%Y-%m', Ad.date_created).label('month'),
        func.sum(Ad.payment_amount).label('total_spending')
    ).join(Campaign, Ad.campaign_id == Campaign.id).filter(Campaign.sponsor_id == id, Ad.is_paid == True).group_by('month').all()
    
    data = [{'month': row.month, 'total_spending': row.total_spending} for row in spending]
    return jsonify(data)

@app.route('/api/sponsors/<int:id>/pending_payments', methods=['GET'])
def get_pending_payments(id):
    pending_payments = db.session.query(
        func.strftime('%Y-%m', Ad.date_created).label('month'),
        func.sum(Ad.payment_amount).label('total_pending')
    ).join(Campaign, Ad.campaign_id == Campaign.id).filter(Campaign.sponsor_id == id, Ad.is_paid == False).group_by('month').all()
    
    data = [{'month': row.month, 'total_pending': row.total_pending} for row in pending_payments]
    return jsonify(data)

@app.route('/api/sponsors/<int:id>/campaign_progress', methods=['GET'])
def get_campaign_progress(id):
    progress = db.session.query(
        Campaign.name,
        ((Campaign.budget - Campaign.remaining_budget) / Campaign.budget * 100).label('progress')
    ).filter(Campaign.sponsor_id == id, Campaign.end_date >= datetime.utcnow()).all()
    
    data = [{'campaign': row.name, 'progress': row.progress} for row in progress]
    return jsonify(data)

# For Admin ----------------------------------------------------------------------------------------------------------------

@app.route('/api/admin/active_users', methods=['GET'])
def get_active_users():
    active_users = db.session.query(
        User.is_deleted,
        func.count(User.id).label('count')
    ).group_by(User.is_deleted).all()
    
    data = [{'status': 'Active Users' if not user.is_deleted else 'Deleted Users', 'count': user.count} for user in active_users]
    return jsonify(data)

@app.route('/api/admin/user_distribution', methods=['GET'])
def get_user_distribution():
    user_distribution = db.session.query(
        User.role,
        func.count(User.id).label('count')
    ).filter(User.role != 'admin').group_by(User.role).all()
    
    data = [{'role': user.role, 'count': user.count} for user in user_distribution]
    return jsonify(data)

@app.route('/api/admin/flagged_campaigns', methods=['GET'])
def get_flagged_campaigns():
    flagged_campaigns = db.session.query(
        Campaign.is_flagged,
        func.count(Campaign.id).label('count')
    ).group_by(Campaign.is_flagged).all()
    
    data = [{'status': 'Flagged Campaigns' if campaign.is_flagged else 'Not Flagged Campaigns', 'count': campaign.count} for campaign in flagged_campaigns]
    return jsonify(data)

@app.route('/api/admin/flagged_users', methods=['GET'])
def get_flagged_users():
    flagged_users = db.session.query(
        User.is_flagged,
        func.count(User.id).label('count')
    ).group_by(User.is_flagged).all()
    
    data = [{'status': 'Flagged Users' if user.is_flagged else 'Not Flagged Users', 'count': user.count} for user in flagged_users]
    return jsonify(data)

@app.route('/api/admin/registered_users_monthly', methods=['GET'])
def get_registered_users_monthly():
    users_monthly = db.session.query(
        func.strftime('%Y-%m', User.date_created).label('month'),
        User.role,
        func.count(User.id).label('count')
    ).group_by('month', User.role).all()
    
    data = [{'month': user.month, 'role': user.role, 'count': user.count} for user in users_monthly]
    return jsonify(data)

@app.route('/api/admin/revenue_monthly', methods=['GET'])
def get_revenue_monthly():
    revenue_monthly = db.session.query(
        func.strftime('%Y-%m', Ad.date_created).label('month'),
        func.sum(Ad.payment_amount).label('total_revenue')
    ).join(Campaign, Ad.campaign_id == Campaign.id
           ).filter(Ad.status == 'accepted', Ad.is_paid == True
                    ).group_by('month').all()
    
    data = [{'month': row.month, 'total_revenue': row.total_revenue} for row in revenue_monthly]
    return jsonify(data)

# --------------------------------------------------------------------------------------------------------------------------
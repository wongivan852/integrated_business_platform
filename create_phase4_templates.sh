#!/bin/bash

# Script to create all Phase 4 templates
# This script creates all remaining HTML templates for Event Management Phase 4

TEMPLATE_DIR="/Users/wongivan/ai_tools/business_tools/integrated_business_platform/templates/event_management"

echo "Creating Phase 4 Templates..."
echo "============================="

# Create feedback_list.html
cat > "$TEMPLATE_DIR/feedback_list.html" << 'EOF'
{% extends "base.html" %}
{% load static %}

{% block title %}Customer Feedback - Krystal Platform{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="fas fa-comments"></i> Customer Feedback</h2>
</div>

<!-- Statistics Cards -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card border-primary">
            <div class="card-body text-center">
                <h3 class="text-primary">{{ total_feedback }}</h3>
                <p class="mb-0">Total Feedback</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-success">
            <div class="card-body text-center">
                <h3 class="text-success">{{ submitted_count }}</h3>
                <p class="mb-0">Submitted</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-warning">
            <div class="card-body text-center">
                <h3 class="text-warning">{{ pending_count }}</h3>
                <p class="mb-0">Pending</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card border-info">
            <div class="card-body text-center">
                <h3 class="text-info">{{ avg_rating|floatformat:1 }}/5.0</h3>
                <p class="mb-0">Avg Rating</p>
            </div>
        </div>
    </div>
</div>

<!-- NPS Score Card -->
<div class="card mb-4">
    <div class="card-body">
        <h5><i class="fas fa-chart-line"></i> Net Promoter Score (NPS)</h5>
        <div class="row mt-3">
            <div class="col-md-3 text-center">
                <h2 class="{% if nps_score >= 50 %}text-success{% elif nps_score >= 0 %}text-warning{% else %}text-danger{% endif %}">
                    {{ nps_score|floatformat:0 }}
                </h2>
                <p>NPS Score</p>
            </div>
            <div class="col-md-3 text-center">
                <h3 class="text-success">{{ promoters }}</h3>
                <p>Promoters</p>
            </div>
            <div class="col-md-3 text-center">
                <h3 class="text-warning">{{ passives }}</h3>
                <p>Passives</p>
            </div>
            <div class="col-md-3 text-center">
                <h3 class="text-danger">{{ detractors }}</h3>
                <p>Detractors</p>
            </div>
        </div>
    </div>
</div>

<!-- Filter -->
<div class="card mb-3">
    <div class="card-body">
        <form method="get" class="row align-items-end">
            <div class="col-md-3">
                <label class="form-label">Status</label>
                <select name="status" class="form-select" onchange="this.form.submit()">
                    <option value="all" {% if status_filter == 'all' %}selected{% endif %}>All</option>
                    <option value="submitted" {% if status_filter == 'submitted' %}selected{% endif %}>Submitted</option>
                    <option value="pending" {% if status_filter == 'pending' %}selected{% endif %}>Pending</option>
                </select>
            </div>
        </form>
    </div>
</div>

<!-- Feedback List -->
<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Event</th>
                        <th>Customer</th>
                        <th>Status</th>
                        <th>Avg Rating</th>
                        <th>NPS</th>
                        <th>Submitted</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for feedback in feedbacks %}
                    <tr>
                        <td>
                            <a href="{% url 'event_management:event_detail' feedback.event.pk %}">
                                {{ feedback.event.event_number }}
                            </a>
                        </td>
                        <td>{{ feedback.customer_name }}</td>
                        <td>
                            {% if feedback.submitted %}
                                <span class="badge bg-success">Submitted</span>
                            {% else %}
                                <span class="badge bg-warning">Pending</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if feedback.submitted %}
                                <span class="badge {% if feedback.average_rating >= 4 %}bg-success{% elif feedback.average_rating >= 3 %}bg-warning{% else %}bg-danger{% endif %}">
                                    {{ feedback.average_rating|floatformat:1 }}/5.0
                                </span>
                            {% else %}
                                -
                            {% endif %}
                        </td>
                        <td>
                            {% if feedback.submitted %}
                                <span class="badge {% if feedback.nps_category == 'promoter' %}bg-success{% elif feedback.nps_category == 'passive' %}bg-warning{% else %}bg-danger{% endif %}">
                                    {{ feedback.nps_category|title }}
                                </span>
                            {% else %}
                                -
                            {% endif %}
                        </td>
                        <td>
                            {% if feedback.submitted_at %}
                                {{ feedback.submitted_at|date:"M d, Y" }}
                            {% else %}
                                -
                            {% endif %}
                        </td>
                        <td>
                            <a href="{% url 'event_management:feedback_detail' feedback.pk %}" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-eye"></i> View
                            </a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="7" class="text-center text-muted">No feedback found</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
EOF

echo "✓ Created feedback_list.html"

# Create feedback_detail.html
cat > "$TEMPLATE_DIR/feedback_detail.html" << 'EOF'
{% extends "base.html" %}
{% load static %}

{% block title %}Feedback Detail - {{ feedback.event.event_number }}{% endblock %}

{% block content %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="{% url 'event_management:feedback_list' %}">Feedback</a></li>
        <li class="breadcrumb-item active">Detail</li>
    </ol>
</nav>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="fas fa-comment-dots"></i> Feedback Detail</h2>
    <a href="{% url 'event_management:event_detail' feedback.event.pk %}" class="btn btn-outline-secondary">
        <i class="fas fa-arrow-left"></i> Back to Event
    </a>
</div>

<!-- Overall Summary -->
<div class="row mb-4">
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h3 class="{% if feedback.average_rating >= 4 %}text-success{% elif feedback.average_rating >= 3 %}text-warning{% else %}text-danger{% endif %}">
                    {{ feedback.average_rating|floatformat:1 }}/5.0
                </h3>
                <p class="mb-0">Overall Average</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h3 class="{% if feedback.nps_category == 'promoter' %}text-success{% elif feedback.nps_category == 'passive' %}text-warning{% else %}text-danger{% endif %}">
                    {{ feedback.likelihood_to_use_again }}/10
                </h3>
                <p class="mb-0">{{ feedback.nps_category|title }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h3 class="{% if feedback.would_recommend %}text-success{% else %}text-danger{% endif %}">
                    {% if feedback.would_recommend %}
                        <i class="fas fa-thumbs-up"></i>
                    {% else %}
                        <i class="fas fa-thumbs-down"></i>
                    {% endif %}
                </h3>
                <p class="mb-0">{% if feedback.would_recommend %}Would Recommend{% else %}Would Not Recommend{% endif %}</p>
            </div>
        </div>
    </div>
</div>

<!-- Event Information -->
<div class="card mb-4">
    <div class="card-header">
        <h5><i class="fas fa-calendar-check"></i> Event Information</h5>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <p><strong>Event Number:</strong> {{ feedback.event.event_number }}</p>
                <p><strong>Event Type:</strong> {{ feedback.event.get_event_type_display }}</p>
                <p><strong>Company:</strong> {{ feedback.event.customer_company }}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Customer:</strong> {{ feedback.customer_name }}</p>
                <p><strong>Email:</strong> {{ feedback.customer_email }}</p>
                <p><strong>Submitted:</strong> {{ feedback.submitted_at|date:"F d, Y g:i A" }}</p>
            </div>
        </div>
    </div>
</div>

<!-- Ratings -->
<div class="card mb-4">
    <div class="card-header">
        <h5><i class="fas fa-star"></i> Service Ratings</h5>
    </div>
    <div class="card-body">
        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center">
                <span>Service Quality:</span>
                <span class="badge bg-{% if feedback.service_quality_rating >= 4 %}success{% elif feedback.service_quality_rating >= 3 %}warning{% else %}danger{% endif %}">
                    {{ feedback.service_quality_rating }}/5
                </span>
            </div>
            <div class="progress mt-1" style="height: 10px;">
                <div class="progress-bar" style="width: {{ feedback.service_quality_rating|mul:20 }}%"></div>
            </div>
        </div>

        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center">
                <span>Staff Professionalism:</span>
                <span class="badge bg-{% if feedback.staff_professionalism_rating >= 4 %}success{% elif feedback.staff_professionalism_rating >= 3 %}warning{% else %}danger{% endif %}">
                    {{ feedback.staff_professionalism_rating }}/5
                </span>
            </div>
            <div class="progress mt-1" style="height: 10px;">
                <div class="progress-bar" style="width: {{ feedback.staff_professionalism_rating|mul:20 }}%"></div>
            </div>
        </div>

        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center">
                <span>Timeliness:</span>
                <span class="badge bg-{% if feedback.timeliness_rating >= 4 %}success{% elif feedback.timeliness_rating >= 3 %}warning{% else %}danger{% endif %}">
                    {{ feedback.timeliness_rating }}/5
                </span>
            </div>
            <div class="progress mt-1" style="height: 10px;">
                <div class="progress-bar" style="width: {{ feedback.timeliness_rating|mul:20 }}%"></div>
            </div>
        </div>

        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center">
                <span>Technical Expertise:</span>
                <span class="badge bg-{% if feedback.technical_expertise_rating >= 4 %}success{% elif feedback.technical_expertise_rating >= 3 %}warning{% else %}danger{% endif %}">
                    {{ feedback.technical_expertise_rating }}/5
                </span>
            </div>
            <div class="progress mt-1" style="height: 10px;">
                <div class="progress-bar" style="width: {{ feedback.technical_expertise_rating|mul:20 }}%"></div>
            </div>
        </div>

        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center">
                <span>Communication:</span>
                <span class="badge bg-{% if feedback.communication_rating >= 4 %}success{% elif feedback.communication_rating >= 3 %}warning{% else %}danger{% endif %}">
                    {{ feedback.communication_rating }}/5
                </span>
            </div>
            <div class="progress mt-1" style="height: 10px;">
                <div class="progress-bar" style="width: {{ feedback.communication_rating|mul:20 }}%"></div>
            </div>
        </div>
    </div>
</div>

<!-- Customer Feedback -->
<div class="card mb-4">
    <div class="card-header">
        <h5><i class="fas fa-comment-dots"></i> Customer Comments</h5>
    </div>
    <div class="card-body">
        <h6 class="text-success">What We Did Well:</h6>
        <p class="bg-light p-3 rounded">{{ feedback.what_did_well|default:"No comments provided." }}</p>

        <h6 class="text-warning mt-3">Areas for Improvement:</h6>
        <p class="bg-light p-3 rounded">{{ feedback.what_can_improve|default:"No comments provided." }}</p>

        <h6 class="text-info mt-3">Additional Comments:</h6>
        <p class="bg-light p-3 rounded">{{ feedback.additional_comments|default:"No comments provided." }}</p>
    </div>
</div>

<!-- Internal Review -->
<div class="card mb-4">
    <div class="card-header">
        <h5><i class="fas fa-user-tie"></i> Internal Review</h5>
    </div>
    <div class="card-body">
        <form method="post" action="{% url 'event_management:feedback_review' feedback.pk %}">
            {% csrf_token %}
            <div class="mb-3">
                <label class="form-label">Internal Notes</label>
                <textarea name="internal_notes" class="form-control" rows="4">{{ feedback.internal_notes }}</textarea>
            </div>

            <div class="mb-3">
                <div class="form-check">
                    <input type="checkbox" name="follow_up_required" class="form-check-input" id="followUpRequired" {% if feedback.follow_up_required %}checked{% endif %}>
                    <label class="form-check-label" for="followUpRequired">
                        Follow-up Required
                    </label>
                </div>
            </div>

            <div class="mb-3">
                <div class="form-check">
                    <input type="checkbox" name="follow_up_completed" class="form-check-input" id="followUpCompleted" {% if feedback.follow_up_completed %}checked{% endif %}>
                    <label class="form-check-label" for="followUpCompleted">
                        Follow-up Completed
                    </label>
                </div>
            </div>

            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save"></i> Save Review
            </button>
        </form>
    </div>
</div>
{% endblock %}
EOF

echo "✓ Created feedback_detail.html"

echo ""
echo "============================="
echo "Phase 4 templates created successfully!"
echo "Run this script to create the remaining templates."
EOF

chmod +x /Users/wongivan/ai_tools/business_tools/integrated_business_platform/create_phase4_templates.sh

echo "Created template generation script"

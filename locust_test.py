from locust import HttpUser, task, between, events
import json
import random
import time

# Test queries across domains
TEST_QUERIES = {
    'hr': [
        "What are the HR benefits?",
        "How do I request leave?",
        "What is the parental leave policy?",
        "How do I enroll in health insurance?"
    ],
    'it': [
        "My laptop is broken",
        "How do I reset my password?",
        "VPN not working",
        "How do I set up VPN access?"
    ],
    'finance': [
        "How do I submit expenses?",
        "What is the expense policy?",
        "How do I get reimbursed?",
        "Submit travel request"
    ],
    'general': [
        "Where is the office?",
        "What are office hours?",
        "How do I contact support?",
        "Company policies"
    ]
}

class HCGDemoUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        self.user_id = f"user_{random.randint(1000, 9999)}"
        self.session_id = f"session_{int(time.time())}_{self.user_id}"
    
    @task(4)
    def query_knowledge_base(self):
        """Simulate KB query (40% of load)"""
        domain = random.choice(list(TEST_QUERIES.keys()))
        query = random.choice(TEST_QUERIES[domain])
        
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": query,
                "user": self.user_id,
                "channel": "C12345",
                "ts": str(time.time())
            }
        }
        
        with self.client.post(
            "/slack/events",
            json=payload,
            catch_response=True,
            name=f"KB Query - {domain}"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def create_ticket(self):
        """Simulate ticket creation (20% of load)"""
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "Create a ticket for VPN issue",
                "user": self.user_id,
                "channel": "C12345",
                "ts": str(time.time())
            }
        }
        
        with self.client.post(
            "/slack/events",
            json=payload,
            catch_response=True,
            name="Create Ticket"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(1)
    def feedback(self):
        """Simulate feedback (10% of load)"""
        payload = {
            "type": "block_actions",
            "actions": [{
                "type": "button",
                "action_id": "feedback_positive",
                "value": "helpful"
            }],
            "user": {"id": self.user_id}
        }
        
        with self.client.post(
            "/slack/interactions",
            json=payload,
            catch_response=True,
            name="Feedback"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

# Custom stats tracking
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Load test starting...")
    print(f"Target: 500 concurrent users")
    print(f"Expected p95 latency: <15s")
    print(f"Expected error rate: <1%")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\nLoad test completed!")
    
    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    
    print(f"\nResults:")
    print(f"  Total Requests: {total_requests}")
    print(f"  Failures: {total_failures}")
    print(f"  Error Rate: {error_rate:.2f}%")
    print(f"  Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"  P95 Response Time: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    
    # Validation
    p95_ok = stats.total.get_response_time_percentile(0.95) < 15000
    error_ok = error_rate < 1.0
    
    print(f"\nValidation:")
    print(f"  {'✅' if p95_ok else '❌'} P95 latency <15s")
    print(f"  {'✅' if error_ok else '❌'} Error rate <1%")

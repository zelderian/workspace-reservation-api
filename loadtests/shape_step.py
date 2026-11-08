from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    stages = [
        (60, 50),
        (120, 100),
        (180, 200),
        (240, 300),
        (300, 400),
    ]
    spawn_rate = 10

    def tick(self):
        run_time = self.get_run_time()
        for end, users in self.stages:
            if run_time < end:
                return users, self.spawn_rate
        return None

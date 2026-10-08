package com.school.sms.seed;

import com.school.sms.config.AdminProperties;
import com.school.sms.model.AppUser;
import com.school.sms.model.Role;
import com.school.sms.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

/** Creates the default administrator on first startup so the API can be bootstrapped. */
@Component
public class AdminSeeder implements CommandLineRunner {

    private static final Logger LOG = LoggerFactory.getLogger(AdminSeeder.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AdminProperties adminProperties;

    public AdminSeeder(UserRepository userRepository, PasswordEncoder passwordEncoder,
                       AdminProperties adminProperties) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.adminProperties = adminProperties;
    }

    @Override
    public void run(String... args) {
        if (userRepository.existsByRole(Role.ADMIN)) {
            LOG.info("Admin user already present, skipping seed");
            return;
        }
        String password = adminProperties.password();
        if (password == null || password.isBlank()) {
            throw new IllegalStateException("app.admin.password must not be blank");
        }
        AppUser admin = new AppUser(adminProperties.username(), passwordEncoder.encode(password), Role.ADMIN);
        userRepository.save(admin);
        LOG.info("Seeded default admin user '{}'", admin.getUsername());
    }
}

function switchToRegister() {
    document.getElementById('mainContainer').classList.add('register-active');
}

function switchToLogin() {
    document.getElementById('mainContainer').classList.remove('register-active');
}

function togglePasswordVisibility(inputId, iconElement) {
    const passwordInput = document.getElementById(inputId);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        iconElement.classList.remove('fa-eye');
        iconElement.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        iconElement.classList.remove('fa-eye-slash');
        iconElement.classList.add('fa-eye');
    }
}
// --doạn hàm thay đổi theme màu em viết có tìm hiểu nhiều nguồn e sẽ trình bày theo cách 
// hiểu của em

// --khi ngươi dùng mới vào trang web lần đầu tiên họ sẽ được set time theo thời gian hiên tại một lần
// --script ở phần head của html để tránh khi load trang sẽ bị nháy sáng theo css light được cài đặt mặc định
// vì sau mỗi lần load nó sẽ lấy html và css đầu tiên
// --hàm onlyThemecho phép cài đặt theme theo thời gian đầu cùng với hàm checkTheme để không bị ghi đè ở mỗi lần load trang
const onlyTheme = () => {
    let root = document.documentElement;
    let themeBtn = document.getElementById('themeToggleBtn');
    let icon = themeBtn.querySelector('i');
    let now = new Date() ;
    let hours = now.getHours() ;
    if (hours >= 18 || hours < 6){
        
        root.setAttribute('data-theme', 'dark');
        localStorage.setItem('selectedTheme', 'dark');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        root.removeAttribute('data-theme');
        localStorage.setItem('selectedTheme', 'light');
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
}
// --hàm applyTheme dể kiểm tra hiện tại trang đang dược lưu bộ nhớ tạm là gì 
// để tránh việc sau mỗi lần load trang sẽ bị mất dữ liệu và set sẵn theme khi load lại trang
const applyTheme = () => {
    let themeBtn = document.getElementById('themeToggleBtn');
    let icon = themeBtn.querySelector('i');
    let theme = localStorage.getItem("selectedTheme");
    if (theme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        document.documentElement.removeAttribute("data-theme");
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
};
const checkTheme = () => {
    
    if (!localStorage.getItem("selectedTheme")) {
        onlyTheme();
    } else {
        applyTheme();
    }
}
checkTheme();
// --bắt sự kiện đổi theme màu khi onclick
// --thay vì khi người dùng click vào và stlye trong js thì e chọn cách chỉnh lại atribute cho html với logic
// ghi đè lại css (root) được cài làm mặc định và ưu tiên cao nhất, nếu cả element html đã có theme=dark([data-theme="dark"]) thì 
// cài đặt lại light bằng cách xóa attribute data-theme, nếu chưa có thì tương đương với việc đang để chế độ light và set lại attribute
// sau đó bước cuối cùng là lưu lại trên localstorega
const toggleTheme = () => {
    let root = document.documentElement;
    let themeBtn = document.getElementById('themeToggleBtn');
    let icon = themeBtn.querySelector('i');
    
    if (root.hasAttribute('data-theme')) {
        root.removeAttribute('data-theme');
        localStorage.setItem('selectedTheme', 'light');
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        root.setAttribute('data-theme', 'dark');
        localStorage.setItem('selectedTheme', 'dark');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
}

document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    alert('Login function in development');
});

document.getElementById('signupForm').addEventListener('submit', function(e) {
    e.preventDefault();
    alert('Sign up function in development');
});

document.querySelectorAll('.social-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        alert('Social login in development');
    });
});
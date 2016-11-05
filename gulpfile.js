var gulp = require('gulp');
var sass = require('gulp-sass');
var browserSync = require('browser-sync').create();

gulp.task('sass', function(){
  return gulp.src('source-files')
    .pipe(sass()) // Using gulp-sass
    .pipe(gulp.dest('destination'))
});

gulp.task('sass', function(){
  return gulp.src('app/static/scss/styles.scss')
    .pipe(sass()) // Converts Sass to CSS with gulp-sass
    .pipe(gulp.dest('app/static/css'))
	.pipe(browserSync.reload({
      stream: true
    }))
});

gulp.task('watch', ['browserSync', 'sass'], function(){
  gulp.watch('app/static/scss/**/*.scss', ['sass']);
  gulp.watch('app/templates/*.html', browserSync.reload); 
  gulp.watch('app/static/js/**/*.js', browserSync.reload); 
})

gulp.task('browserSync', function() {
  browserSync.init({
        proxy: {
            target: "http://127.0.0.1:5000/"
        },
        reloadDelay: 300
    })
})